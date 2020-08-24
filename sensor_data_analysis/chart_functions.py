import matplotlib.pyplot as plt

# initialize chart with sizes, title and labels
def init_chart(title, xlabel, ylabel, xsize, ysize):
    fig, ax = plt.subplots(figsize=(xsize, ysize))
    ax.set(title = title, ylabel = ylabel, xlabel = xlabel)
    return fig, ax

# prepare chart (place legend, layout) for saving to pdf
def save_chart_to_file(fig, pp):
    fig.legend(loc="upper right", bbox_to_anchor=(0.95, 0.95))
    fig.tight_layout()
    pp.savefig(fig)

# encapsulate in functions all the created charts
########################################################################
def create_title_page(xsize, ysize, pp, title):
    fig, ax = plt.subplots(figsize = (xsize, ysize))
    ax.axis("off")
    fig.text(0.5, 0.5, title, ha = "center", va = "center", fontsize = 28)
    pp.savefig()

def create_histogram_chart(xsize, ysize, pp, df_mean, df_min, df_max, title, xlabel):
    fig, ax = plt.subplots(1, 3, figsize = (xsize, ysize))
    ax[0].set(title = title + " mean histogram", xlabel = xlabel, ylabel = "Frequency (days)")
    ax[1].set(title = title + " min histogram", xlabel = xlabel, ylabel = "Frequency (days)")
    ax[2].set(title = title + " max histogram", xlabel = xlabel, ylabel = "Frequency (days)")

    df_mean["value"].hist(ax = ax[0], bins = int(df_max["value"].max() - df_min["value"].min()))
    df_min["value"].hist(ax = ax[1], bins = int(df_max["value"].max() - df_min["value"].min()))
    df_max["value"].hist(ax = ax[2], bins = int(df_max["value"].max() - df_min["value"].min()))

    fig.tight_layout()
    pp.savefig(fig)

def create_indoor_outdoor_chart(xsize, ysize, pp, data_outdoor_mean, data_indoor_mean):
    fig, ax1 = init_chart("Indoor-Outdoor temperature", "Time", "Celsius Degrees", xsize, ysize)

    data_outdoor_mean["value"].plot(ax = ax1, label = "Outdoor")
    data_indoor_mean["value"].plot(ax = ax1, label = "Indoor")

    save_chart_to_file(fig, pp)

def create_heat_index_chart(xsize, ysize, pp, data_heatindex):
    fig, ax1 = init_chart("Outdoor Heat index", "Time", "Celsius Degrees", xsize, ysize)
    start = 0
    legend_labels = set()
    for index in range(0, len(data_heatindex["color"]) - 1):
        if (data_heatindex["color"][index] != data_heatindex["color"][index + 1]) or (index == len(data_heatindex["color"]) - 2):
            end = index + 1
            if data_heatindex["color"][index] not in legend_labels:
                color = data_heatindex["color"][index]
                legend_labels.add(color)
                if color == "green":
                    my_label = "< 27"
                elif color == "yellow":
                    my_label = "[27:32]"
                elif color == "orange":
                    my_label = "[32:41]"
                elif color == "red":
                    my_label = "> 41"
            else:
                my_label = ""
            ax1.fill_between(data_heatindex.index[start : end + 1], data_heatindex["value"][start : end + 1], step = "post", color = data_heatindex["color"][start], label = my_label)
            start = index + 1

    save_chart_to_file(fig, pp)

def create_temp_min_max_chart(xsize, ysize, pp, name, data_temp_mean, data_temp_max, data_temp_min):
    fig, ax1 = init_chart(name + " MIN/MAX temperature", "Time", "Celsius Degrees", xsize, ysize)

    ax1.fill_between(data_temp_max.index, data_temp_max["value"], data_temp_min["value"], label = "Min-Max")
    ax1.plot(data_temp_max.index, data_temp_mean["value"], color = "white", label = "Mean")

    save_chart_to_file(fig, pp)

def create_humidity_pressure_chart(xsize, ysize, pp, data_humidity_mean, data_pressure_mean):
    fig, ax1 = init_chart("Humidity-Pressure", "Time", "Celsius Degrees", xsize, ysize)
    ax2 = ax1.twinx()
    ax2.set_ylabel("Pa", color = "tab:orange")

    data_humidity_mean["value"].plot(ax = ax1, label = "Humidity")
    data_pressure_mean["value"].plot(ax = ax2, color = "tab:orange", label = "Pressure")

    save_chart_to_file(fig, pp)

def create_windows_chart(xsize, ysize, pp, data_window_left, data_window_right, data_outdoor_mean):
    fig, ax1 = init_chart("Window Living Left", "Time", "Open hours", xsize, ysize)
    ax2 = ax1.twinx()
    ax2.set_ylabel("Celsius Degrees", color = "tab:orange")

    data_window_left["state"].plot(ax = ax1, label = "Window LEFT")
    data_window_right["state"].plot(ax = ax1, label = "Window RIGHT")
    # ~ ax1.axhline(y = 30 * 24, label = "Max")
    data_outdoor_mean["value"].plot(ax = ax2, color = "tab:orange", label = "Outdoor temp")

    save_chart_to_file(fig, pp)

def create_table_samples(xsize, ysize, pp, df):
    fig, ax = plt.subplots(2, figsize=(xsize, ysize))
    fig.suptitle("Sample Statistics")
    ax[0].axis("off")
    ax[1].axis("off")

    r,c = df.shape
    ax[0].table(cellText = df.values, rowLabels = df.index, colLabels = df.columns, colColours = ["lightgray"] * c, bbox=[0,0,1,1])
    pp.savefig(fig)
