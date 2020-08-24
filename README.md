# sensor_data_analysis
Analysis and report creating, containing charts and tables from collected data from various sensors

## Description 

The purpose is to analyze and and aggregate the collected data from different sensors. The acquisition software used is https://github.com/Vlad-Mocanu/RaspbiAtHome.
All the sampled data is stored in a MySQL DB on a different host. For the current project, accessing the data has been done via an SSH tunnel.
After accessing the database, the samples are cleaned (trim spikes from sensors), resample them to be able to create the overview and interpolate the samples in case of sensor malfunction or power-down.

<img src="System Overview.png">

Several plots are generated and saved as a report in a pdf file (or multiple files - the report is done on yearly basis):
- Sample statistics
- Outdoor temperature histograms
- Indoor vs Outdoor temperature
- Outdoor heatindex (temperature and humidity) https://en.wikipedia.org/wiki/Heat_index 
- Windows open/closed state vs Outdoor temperature
- etc.

## Requirements

To install the package and its dependencies, you can run:
```
git clone https://github.com/Vlad-Mocanu/sensor_data_analysis/
pip install sensor_data_analysis/
````

## Usage

After you navigate to sensor_data_analysis/sensor_data_analysis, in order to run, you can use:
```
python sensor_data_analysis.py
```
    
The default configuration file is sensor_data_analysis/sensor_data_analysis/sensors_config.json. This file can be edited to adjust the program to your needs. In order to use another configuration file, other than the default one you can run it like this:
```
python sensor_data_analysis.py --config_file <path_to_config_file>
```
