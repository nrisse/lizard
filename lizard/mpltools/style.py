"""
Definition of styles and constants for this project.
"""

import matplotlib as mpl
import matplotlib.colors as mcolors
import numpy as np

__all__ = [
    "missions",
    "sensors",
    "viewing_angles",
    "platform_colors",
    "pol_markers",
    "flight_colors",
    "sensor_colors",
    "flight_colors2",
    "kmeans_colors",
    "hamp_cols",
    "mirac_hatpro_cols",
    "mirac_cols",
]

# matplotlib style
mpl.rcParams["axes.spines.right"] = False
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["figure.constrained_layout.use"] = True
mpl.rcParams["figure.figsize"] = [5, 4]
mpl.rcParams["savefig.dpi"] = 300
mpl.rcParams["savefig.bbox"] = "tight"

# field campaign time periods
missions = {
    "ACLOUD": {
        "start": np.datetime64("2017-05-23"),
        "end": np.datetime64("2017-06-26"),
    },
    "AFLUX": {
        "start": np.datetime64("2019-03-19"),
        "end": np.datetime64("2019-04-11"),
    },
    "MOSAiC-ACA": {
        "start": np.datetime64("2020-08-30"),
        "end": np.datetime64("2020-09-13"),
    },
    "HALO-AC3": {
        "start": np.datetime64("2022-03-12"),
        "end": np.datetime64("2022-04-12"),
    },
}

# instrumentation
sensors = {  # sensors for each campaign
    "ACLOUD": {"P5": dict(sensor1="MiRAC-A", sensor2="MiRAC-P")},
    "AFLUX": {"P5": dict(sensor1="MiRAC-A", sensor2="MiRAC-P")},
    "MOSAiC-ACA": {"P5": dict(sensor1="MiRAC-A", sensor2="HATPRO")},
    "HALO-AC3": {
        "P5": dict(sensor1="MiRAC-A", sensor2="HATPRO"),
        "HALO": dict(sensor1="HAMP", sensor2=None),
    },
}

viewing_angles = {  # channel viewing angles for each campaign by sensor order
    "ACLOUD": {"P5": [-25, 0, 0, 0, 0, 0, 0, 0, 0]},
    "AFLUX": {"P5": [-25, 0, 0, 0, 0, 0, 0, 0, 0]},
    "MOSAiC-ACA": {"P5": [-25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    "HALO-AC3": {
        "P5": [-25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "HALO": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
    },
}

# colors
# colormap for 22 GHz
ncol = 7
norm = mcolors.Normalize(0, 1)
colors = [
    [norm(0), "#BFAA00"],
    [norm(0.33), "#2CA400"],
    [norm(0.67), "#00776A"],
    [norm(1.0), "#00467B"],
]
cmap = mcolors.LinearSegmentedColormap.from_list("", colors)
cmap_22ghz = [
    mcolors.to_hex(cmap(i)) for i in np.linspace(0, 255, ncol).astype("int")
]

# colormap for 56 GHz
ncol = 7
norm = mcolors.Normalize(0, 1)
colors = [
    [norm(0), "#BFAA00"],
    [norm(0.33), "#2CA400"],
    [norm(0.67), "#00776A"],
    [norm(1.0), "#112383"],
]
cmap = mcolors.LinearSegmentedColormap.from_list("", colors)
cmap_56ghz = [
    mcolors.to_hex(cmap(i)) for i in np.linspace(0, 255, ncol).astype("int")
]

# colormap for 183 GHz
ncol = 6
norm = mcolors.Normalize(0, 1)
colors = [
    [norm(0), "#BF7F00"],
    [norm(0.33), "#2CA400"],
    [norm(0.67), "#00776A"],
    [norm(1.0), "#00467B"],
]
cmap = mcolors.LinearSegmentedColormap.from_list("", colors)
cmap_183ghz = [
    mcolors.to_hex(cmap(i)) for i in np.linspace(0, 255, ncol).astype("int")
]

# individual frequencies coarse (use from label strings)
rad_cols_coarse = {
    "88": "#519700",
    "89": "#519700",
    "90": "#519700",
    "91": "#519700",
    "150": "gray",
    "157": "gray",
    "165": "gray",
    "183": "#00467B",
    "190": "#00467B",
    "243": "k",
    "340": "k",
}

# radiometers: MiRAC-A + MiRAC-P
mirac_cols = {
    1: "#519700",
    2: "#bf7f00",
    3: "#669500",
    4: "#239b16",
    5: "#098054",
    6: "#006471",
    7: "#00467b",
    8: "#FF6D27",
    9: "#63016D",
}

# radiometers: MiRAC-A + HATPRO
mirac_hatpro_cols = {
    1: "#519700",
    2: "#8c96c6",
    3: cmap_22ghz[1],
    4: cmap_22ghz[2],
    5: cmap_22ghz[3],
    6: cmap_22ghz[4],
    7: cmap_22ghz[5],
    8: "#88419d",
    9: "#6e016b",
    10: cmap_56ghz[5],
    11: cmap_56ghz[4],
    12: cmap_56ghz[3],
    13: cmap_56ghz[2],
    14: cmap_56ghz[1],
    15: cmap_56ghz[0],
}

# radiometer: hamp
hamp_cols = {
    1: "#8c96c6",
    2: cmap_22ghz[1],
    3: cmap_22ghz[2],
    4: cmap_22ghz[3],
    5: cmap_22ghz[4],
    6: cmap_22ghz[5],
    7: "#88419d",
    8: "#6e016b",
    9: cmap_56ghz[5],
    10: cmap_56ghz[4],
    11: cmap_56ghz[3],
    12: cmap_56ghz[2],
    13: cmap_56ghz[1],
    14: cmap_56ghz[0],
    15: "#519700",
    16: "#feedde",
    17: "#fdbe85",
    18: "#fd8d3c",
    19: "#d94701",
    20: "#bf7f00",
    21: "#669500",
    22: "#239b16",
    23: "#098054",
    24: "#006471",
    25: "#00467b",
}

# individual frequencies
rad_cols = {
    89000: "#519700",
    183910: cmap_183ghz[0],
    184810: cmap_183ghz[1],
    185810: cmap_183ghz[2],
    186810: cmap_183ghz[3],
    188310: cmap_183ghz[4],
    190810: cmap_183ghz[5],
    243000: "#FF6D27",
    340000: "#63016D",
    22240: cmap_22ghz[0],
    23040: cmap_22ghz[1],
    23840: cmap_22ghz[2],
    25440: cmap_22ghz[3],
    26240: cmap_22ghz[4],
    27840: cmap_22ghz[5],
    31400: cmap_22ghz[6],
    51260: cmap_56ghz[6],
    52280: cmap_56ghz[5],
    53860: cmap_56ghz[4],
    54940: cmap_56ghz[3],
    56660: cmap_56ghz[2],
    57300: cmap_56ghz[1],
    58000: cmap_56ghz[0],
}

# research flight colors
flight_colors = {
    "ACLOUD_P5_RF04": "#000000",
    "ACLOUD_P5_RF05": "#000000",
    "ACLOUD_P5_RF06": "#000000",
    "ACLOUD_P5_RF07": "#000000",
    "ACLOUD_P5_RF08": "#000000",
    "ACLOUD_P5_RF10": "#1f77b4",
    "ACLOUD_P5_RF11": "#000000",
    "ACLOUD_P5_RF13": "#000000",
    "ACLOUD_P5_RF14": "#ff7f0e",
    "ACLOUD_P5_RF15": "#000000",
    "ACLOUD_P5_RF16": "#000000",
    "ACLOUD_P5_RF17": "#2ca02c",
    "ACLOUD_P5_RF18": "#000000",
    "ACLOUD_P5_RF19": "#000000",
    "ACLOUD_P5_RF20": "#000000",
    "ACLOUD_P5_RF21": "#000000",
    "ACLOUD_P5_RF22": "#000000",
    "ACLOUD_P5_RF23": "#d62728",
    "ACLOUD_P5_RF25": "#9467bd",
    "AFLUX_P5_RF02": "#000000",
    "AFLUX_P5_RF03": "#000000",
    "AFLUX_P5_RF04": "#000000",
    "AFLUX_P5_RF05": "#000000",
    "AFLUX_P5_RF06": "#8c564b",
    "AFLUX_P5_RF07": "#e377c2",
    "AFLUX_P5_RF08": "#7f7f7f",
    "AFLUX_P5_RF09": "#000000",
    "AFLUX_P5_RF10": "#000000",
    "AFLUX_P5_RF11": "#000000",
    "AFLUX_P5_RF12": "#000000",
    "AFLUX_P5_RF13": "#bcbd22",
    "AFLUX_P5_RF14": "#17becf",
    "AFLUX_P5_RF15": "#058B7D",
    "MOSAiC-ACA_P5_RF02": "#000000",
    "MOSAiC-ACA_P5_RF03": "#000000",
    "MOSAiC-ACA_P5_RF04": "#000000",
    "MOSAiC-ACA_P5_RF05": "#000000",
    "MOSAiC-ACA_P5_RF06": "#000000",
    "MOSAiC-ACA_P5_RF07": "#000000",
    "MOSAiC-ACA_P5_RF08": "#000000",
    "MOSAiC-ACA_P5_RF09": "#000000",
    "MOSAiC-ACA_P5_RF10": "#000000",
    "MOSAiC-ACA_P5_RF11": "#000000",
}

flight_colors2 = {
    "ACLOUD_P5_RF23": "#2a9d8f",
    "ACLOUD_P5_RF25": "#264653",
    "AFLUX_P5_RF07": "#d4a373",
    "AFLUX_P5_RF08": "#e9c46a",
    "AFLUX_P5_RF13": "#ffb703",
    "AFLUX_P5_RF14": "#f4a261",
    "AFLUX_P5_RF15": "#e76f51",
}

# satellite colors (brown for Metop, blue for NOAA and SNPP, green for DMSP)
platform_colors = {
    "Aqua": {"color": "rosybrown", "linestyle": "-"},
    "Metop-A": {"color": "peru", "linestyle": "-"},
    "Metop-B": {"color": "sandybrown", "linestyle": "-"},
    "Metop-C": {"color": "saddlebrown", "linestyle": "-"},
    "NOAA-15": {"color": "dodgerblue", "linestyle": "-"},
    "NOAA-18": {"color": "deepskyblue", "linestyle": "-"},
    "NOAA-19": {"color": "aqua", "linestyle": "-"},
    "NOAA-20": {"color": "teal", "linestyle": "-"},
    "SNPP": {"color": "navy", "linestyle": "-"},
    "GCOM-W": {"color": "violet", "linestyle": "--"},
    "DMSP-F15": {"color": "forestgreen", "linestyle": "--"},
    "DMSP-F16": {"color": "limegreen", "linestyle": "-."},
    "DMSP-F17": {"color": "mediumseagreen", "linestyle": "-."},
    "DMSP-F18": {"color": "lime", "linestyle": "-."},
    "Polar 5": {"color": "darkgray", "linestyle": "-"},
}

# sensor colors (derived from platform colors)
sensor_colors = {
    "MHS": "saddlebrown",
    "ATMS": "navy",
    "SSMIS": "mediumseagreen",
    "AMSR2": "violet",
    "MiRAC": "black",
}

pol_markers = {
    0: {"label": "VH", "marker": "o"},
    1: {"label": "QV", "marker": "d"},
    2: {"label": "QH", "marker": "D"},
    3: {"label": "V", "marker": "v"},
    4: {"label": "H", "marker": "h"},
    5: {"label": "S3", "marker": "o"},
    6: {"label": "S4", "marker": "o"},
    7: {"label": "xVH", "marker": "o"},
}

# k-means cluster colors
kmeans_colors = {1: "#2E4272", 2: "#FFB631", 3: "#479030", 4: "#BA459D"}
