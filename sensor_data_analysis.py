import argparse
import json
import pymysql
import pandas as pd
import numpy as np
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
from sshtunnel import SSHTunnelForwarder

import chart_functions

# returns a string with the full query containing the date filtering (year, month, day)
def get_query(table, filter_dict):
    query = "SELECT * FROM %s" % table

    if (len(filter_dict) > 0):
        query = "%s WHERE" % query

        for i, key in enumerate(filter_dict):
            assert (len(filter_dict[key]) == 2), "Number of filter items must be 2 (lower limit and upper limit)"
            assert (filter_dict[key][0] <= filter_dict[key][1]), "Bad %s argumets" % key

            if (key == "year"):
                query = "%s YEAR(date) >= %0d && YEAR(date) <= %0d" % (query, filter_dict[key][0], filter_dict[key][1])
            elif (key == "month"):
                query = "%s MONTH(date) >= %0d && MONTH(date) <= %0d" % (query, filter_dict[key][0], filter_dict[key][1])
            elif (key == "day"):
                query = "%s DAY(date) >= %0d && DAY(date) <= %0d" % (query, filter_dict[key][0], filter_dict[key][1])
            else:
                assert 0, "Unable to handle filter type"

            if (i != len(filter_dict) - 1):
                query = "%s &&" % (query)

    query = "%s;" % query
    return query

# returns a data frame based on the table the data is stored in MySQL and the date filter (to form the query)
def get_data_from_sql(table, filter_dict, conn):
    query = get_query(table, filter_dict)
    print("query = %s" % query)
    return pd.read_sql_query(query, conn, index_col="date")

# used to clean the data (trim values lower or higher than some tresholds) and return the resampled data for mean, min and max
def get_clean_data(df, resample_rule, my_filter = None):
    if my_filter != None:
        assert (len(my_filter) == 2), "Number of filter items must be 2 (lower limit and upper limit)"
        assert (my_filter[0] <= my_filter[1]), "Bad argumets: %d must be lower or equal to %d" % (my_filter[0], my_filter[1])
        df["value"] = df["value"].apply(lambda x: np.NaN if x < my_filter[0] or x > my_filter[1] else x)
    # the sensors might produce spikes and we can end up with the same date (which created problems when we use it as index)
    # remove index duplicates and create equal spaced samples (one per hour)
    df = df[~df.index.duplicated(keep = "last")]
    df = df.resample("H").ffill();
    df["value"] = df["value"].interpolate(method = "linear")

    return df.resample(resample_rule).mean(), df.resample(resample_rule).min(), df.resample(resample_rule).max()

# transform the unqual spaced data (for windows) to equal spaced data (which has been cleaned and resampled)
def get_clean_equal_spaced_data(df, resample_rule):
    # the sensors might produce spikes and we can end up with the same date (which created problems when we use it as index)
    # remove index duplicates and create equal spaced samples (one per hour)
    df = df[~df.index.duplicated(keep="last")]
    df = df.resample("H").ffill()

    # create a sample per day which sums the 1hour equaly spaced samples
    return df.resample(resample_rule).sum()

# the heatindex is a how humidity influences the felt temperature
def compute_heat_index(df_temperature, df_humidity, c):
    # join the outdoor temp data with the humidity to start calculations
    data_heatindex = data_outdoor_mean.join(data_humidity_mean, on = "date", lsuffix = "temp", rsuffix = "humid")
    # the applied formula is for F degees while the measurments are in C degrees
    data_heatindex["valuetemp_f"] = (data_heatindex["valuetemp"] * 9 / 5) + 32
    data_heatindex["value"] = np.where(data_heatindex["valuetemp"] >= 21,
        (c["c1"] + c["c2"] * data_heatindex["valuetemp_f"] + \
        c["c3"] * data_heatindex["valuehumid"] + c["c4"] * data_heatindex["valuetemp_f"] * data_heatindex["valuehumid"] + \
        c["c5"] * (data_heatindex["valuetemp_f"] ** 2) + c["c6"] * (data_heatindex["valuehumid"] ** 2) + \
        c["c7"] * (data_heatindex["valuetemp_f"] ** 2) * data_heatindex["valuehumid"] + \
        c["c8"] * data_heatindex["valuetemp_f"] * (data_heatindex["valuehumid"] ** 2) + \
        c["c9"] * (data_heatindex["valuetemp_f"] ** 2) * (data_heatindex["valuehumid"] ** 2) - 32) * 5/9 , data_heatindex["valuetemp"])
    # heatindex makes sense to be applied when temperatures are high May-Octomber
    data_heatindex = data_heatindex.loc[str(year) + "-05-01" : str(year) + "-10-01"]

    ## apply color labels in order to be able to know the color of the segements when creating the chart
    data_heatindex.loc[(data_heatindex["value"] < 27), "color"] = "green"
    data_heatindex.loc[(data_heatindex["value"] >= 27) & (data_heatindex["value"] < 32), "color"] = "yellow"
    data_heatindex.loc[(data_heatindex["value"] >= 32) & (data_heatindex["value"] < 41), "color"] = "orange"
    data_heatindex.loc[(data_heatindex["value"] >= 41), "color"] = "red"

    return data_heatindex

# read configuration
parser = argparse.ArgumentParser()
parser.add_argument("--config_file", "-f", default="analysis_config.json", help="path to configuration json file (default: analysis_config.json)")
args = parser.parse_args()

with open(args.config_file) as data_file:
    config_options = json.load(data_file)
data_file.close()

matplotlib.style.use(config_options["charts"]["style"])

for year in range(config_options["charts"]["start_report_year"], config_options["charts"]["end_report_year"] + 1):

    pp = PdfPages("sensors_analysis_report_" + str(year) + ".pdf")

    #get raw data from SQL via SSH -> to be removed and replaced with REST call (if there is a REST server)
    ########################################################################
    with SSHTunnelForwarder((config_options["ssh"]["server"], config_options["ssh"]["port"]), ssh_username = config_options["ssh"]["user"],
        ssh_password = config_options["ssh"]["password"], remote_bind_address = (config_options["mysql"]["server"], config_options["mysql"]["port"])) as tunnel:

        conn = pymysql.connect(host = config_options["mysql"]["server"], user = config_options["mysql"]["user"], passwd = config_options["mysql"]["password"],
            db = config_options["mysql"]["database"], port = tunnel.local_bind_port)

        date_filter = {"year": [year, year]}#, "month": [8, 8], "day": [21, 21]}

        data_temperature = get_data_from_sql("temperature", date_filter, conn)
        data_humidity = get_data_from_sql("humidity", date_filter, conn)
        data_pressure = get_data_from_sql("pressure", date_filter, conn)
        data_windows = get_data_from_sql("windows", date_filter, conn)

        conn.close()

    #process and clear SQL data (prepare for charts)
    ########################################################################
    data_outdoor = data_temperature.loc[data_temperature["name"] == "Outdoor Unit"]
    data_indoor = data_temperature.loc[data_temperature["name"] == "Indoor Living"]
    data_window_left = data_windows.loc[data_windows["name"] == "Living LEFT"]
    data_window_right = data_windows.loc[data_windows["name"] == "Living RIGHT"]

    sample_statistics = pd.DataFrame(columns=["Outdoor temp", "Indoor temp", "Humidity", "Pressure", "Window Left", "Window Right"])
    sample_statistics.loc["Collected samples"] = [len(data_outdoor), len(data_indoor), len(data_humidity), len(data_pressure), len(data_window_left), len(data_window_right)]

    data_window_left = get_clean_equal_spaced_data(data_window_left, "M")
    data_window_right = get_clean_equal_spaced_data(data_window_right, "M")

    data_outdoor_mean, data_outdoor_min, data_outdoor_max = get_clean_data(data_outdoor, "D")
    data_outdoor_mean_month, data_outdoor_min_month, data_outdoor_max_month = get_clean_data(data_outdoor, "M")
    data_indoor_mean, data_indoor_min, data_indoor_max = get_clean_data(data_indoor, "D", [config_options["data"]["min_indoor_temp"], config_options["data"]["max_indoor_temp"]])
    data_humidity_mean, data_humidity_min, data_humidity_max = get_clean_data(data_humidity, "D", [config_options["data"]["min_humidity"], config_options["data"]["max_humidity"]])
    data_pressure_mean, data_pressure_min, data_pressure_max = get_clean_data(data_pressure, "D", [config_options["data"]["min_pressure"], config_options["data"]["max_pressure"]])

    c = config_options["charts"]["heat_index_coef"]
    data_heatindex = compute_heat_index(data_outdoor_mean, data_humidity_mean, c)

    sample_statistics.loc["Used samples"] = [len(data_outdoor_mean), len(data_indoor_mean), len(data_humidity_mean), len(data_pressure_mean), len(data_window_left), len(data_window_right)]
    sample_statistics.loc["Min"] = ["%.1f" % data_outdoor_min["value"].min(), "%.1f" % data_indoor_min["value"].min(), data_humidity_min["value"].min(), data_pressure_min["value"].min(), "-", "-"]
    sample_statistics.loc["Max"] = ["%.1f" % data_outdoor_max["value"].max(), "%.1f" % data_indoor_max["value"].max(), data_humidity_max["value"].max(), data_pressure_max["value"].max(), "-", "-"]

    #create charts
    ########################################################################
    xsize = config_options["charts"]["xfig_size"]
    ysize = config_options["charts"]["yfig_size"]
    chart_functions.create_title_page(xsize, ysize, pp, "Sensor data report - " + str(year))
    chart_functions.create_table_samples(xsize, ysize, pp, sample_statistics)
    chart_functions.create_histogram_chart(xsize, ysize, pp, data_outdoor_mean, data_outdoor_min, data_outdoor_max, "Outdoor temperature", "Celsius Degrees")
    chart_functions.create_indoor_outdoor_chart(xsize, ysize, pp, data_outdoor_mean, data_indoor_mean)
    chart_functions.create_temp_min_max_chart(xsize, ysize, pp, "Indoor", data_indoor_mean, data_indoor_max, data_indoor_min)
    chart_functions.create_temp_min_max_chart(xsize, ysize, pp, "Outdoor", data_outdoor_mean, data_outdoor_max, data_outdoor_min)
    chart_functions.create_heat_index_chart(xsize, ysize, pp, data_heatindex)
    chart_functions.create_humidity_pressure_chart(xsize, ysize, pp, data_humidity_mean, data_pressure_mean)
    chart_functions.create_windows_chart(xsize, ysize, pp, data_window_left, data_window_right, data_outdoor_mean_month)

    pp.close()
    print("Finished creating sensors_analysis_report_" + str(year) + ".pdf")
