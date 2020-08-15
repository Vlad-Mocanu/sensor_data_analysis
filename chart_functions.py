import matplotlib.pyplot as plt

def init_chart(title, xlabel, ylabel, xsize, ysize):
    fig, ax = plt.subplots(figsize=(xsize, ysize))
    ax.set(title = title, ylabel = ylabel, xlabel = xlabel)
    return fig, ax

def save_chart_to_file(fig, pp):
    fig.legend(loc='upper right', bbox_to_anchor=(0.95, 0.95))
    fig.tight_layout()
    pp.savefig(fig)

def create_indoor_outdoor_chart(xsize, ysize, pp, data_outdoor_mean, data_indoor_mean):
    fig, ax1 = init_chart("Indoor-Outdoor temperature", "Time", "Celsius Degrees", xsize, ysize)

    data_outdoor_mean['value'].plot(ax = ax1, label = "Outdoor")
    data_indoor_mean['value'].plot(ax = ax1, label = "Indoor")

    save_chart_to_file(fig, pp)

def create_heat_index_chart(xsize, ysize, pp, data_heatindex):
    fig, ax1 = init_chart("Outdoor Heat index", "Time", "Celsius Degrees", xsize, ysize)

    start = 0
    for index in range(0, len(data_heatindex['color']) - 1):
        if (data_heatindex['color'][index] != data_heatindex['color'][index + 1]) or (index == len(data_heatindex['color']) - 2):
            end = index + 1
            ax1.fill_between(data_heatindex.index[start : end + 1], data_heatindex['value'][start : end + 1], step="post", color=data_heatindex['color'][start], label='')
            start = index + 1

    save_chart_to_file(fig, pp)

def create_indoor_min_max_chart(xsize, ysize, pp, data_indoor_mean, data_indoor_max, data_indoor_min):
    fig, ax1 = init_chart("Indoor MIN/MAX temperature", "Time", "Celsius Degrees", xsize, ysize)

    ax1.fill_between(data_indoor_max.index, data_indoor_max['value'], data_indoor_min['value'], label = "Min-Max")
    ax1.plot(data_indoor_max.index, data_indoor_mean['value'], color = 'white', label = "Mean")

    save_chart_to_file(fig, pp)

def create_humidity_pressure_chart(xsize, ysize, pp, data_humidity_mean, data_pressure_mean):
    fig, ax1 = init_chart("Humidity-Pressure", "Time", "Celsius Degrees", xsize, ysize)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Pa', color = 'tab:orange')

    data_humidity_mean['value'].plot(ax = ax1, label = "Humidity")
    data_pressure_mean['value'].plot(ax = ax2, color = 'tab:orange', label = "Pressure")

    save_chart_to_file(fig, pp)

def create_windows_chart(xsize, ysize, pp, data_window_left, data_window_right, data_outdoor_mean):
    fig, ax1 = init_chart("Window Living Left", "Time", "Open hours", xsize, ysize)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Celsius Degrees', color = 'tab:orange')

    data_window_left['state'].plot(ax = ax1, label = "Window LEFT")
    data_window_right['state'].plot(ax = ax1, label = "Window RIGHT")
    # ~ ax1.axhline(y = 30 * 24, label = "Max")
    data_outdoor_mean['value'].plot(ax = ax2, color = 'tab:orange', label = "Outdoor temp")

    save_chart_to_file(fig, pp)
