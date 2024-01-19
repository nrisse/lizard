"""
Library of functions to simplify access to ac3airborne flight segments.
"""

import ac3airborne
import numpy as np
import pandas as pd
import xarray as xr

META = ac3airborne.get_flight_segments()


def meta(flight_id):
    """
    Jump directly to flight
    """

    mission, platform, name = flight_id.split("_")

    return META[mission][platform][flight_id]


def segments_plain(flight_id):
    """
    Write segments into plain list.
    """

    flight = meta(flight_id)

    s = []

    for segment in flight["segments"]:
        if "parts" in segment.keys():
            for part in segment["parts"]:
                s.append(part)
        else:
            s.append(segment)

    return s


def segment_slice(segment_id):
    """
    Slices from start to end of flight segment
    """

    flight_id = "_".join(segment_id.split("_")[:3])
    segments = segments_dict(flight_id)
    segment = segments[segment_id]

    return slice(
        np.datetime64(segment["start"]), np.datetime64(segment["end"])
    )


def segment_times(segment_id):
    """
    Slices from start to end of flight segment
    """

    flight_id = "_".join(segment_id.split("_")[:3])
    segments = segments_dict(flight_id)
    segment = segments[segment_id]

    return (np.datetime64(segment["start"]), np.datetime64(segment["end"]))


def segments_dict(flight_id):
    """
    Write flight segments into a plain dictionary, with segment id as key.
    Parts are also on first level.
    """

    flight = meta(flight_id)

    s = dict()

    for segment in flight["segments"]:
        if "parts" in segment.keys():
            for part in segment["parts"]:
                if "segment_id" in part.keys():
                    s[part["segment_id"]] = part

        else:
            if "segment_id" in segment.keys():
                s[segment["segment_id"]] = segment

    return s


def remove_segments(ds, flight_id, segment_names):
    """
    Remove certain flight segments from dataset.
    """

    s_flt = [
        s
        for s in segments_plain(flight_id)
        if not np.any(np.isin(s["kinds"], segment_names))
    ]

    ds_sel = None

    for i, s in enumerate(s_flt):
        if i == 0:
            ds_sel = ds.sel(time=slice(s["start"], s["end"]))

        else:
            ds_sel = xr.concat(
                [ds_sel, ds.sel(time=slice(s["start"], s["end"]))], dim="time"
            )

    return ds_sel


def print_segments(flight_id):
    """
    Prints all segments
    """

    flight = meta(flight_id)

    for i, segment in enumerate(flight["segments"]):
        print(
            i,
            ":",
            segment.get("name"),
            segment.get("segment_id"),
            segment.get("kinds"),
        )


def profiles(flight_id):
    """
    Returns list of segments that are either ascents or descents.
    """

    flight = meta(flight_id)

    segment_kinds = [
        "major_ascent",
        "major_descent",
        "small_ascent",
        "small_descent",
        "medium_ascent",
        "medium_descent",
        "large_ascent",
        "large_descent",
        "sawtooth_pattern",
        "racetrack_pattern",
        "stairstep_pattern",
        "ascent",
        "descent",
    ]

    segments = []
    for segment in flight["segments"]:
        for kind in segment["kinds"]:
            if kind in segment_kinds:
                parts = segment.get("parts")
                if parts:
                    for part in parts:
                        for kind in part["kinds"]:
                            if kind in segment_kinds:
                                segments.append(part)
                else:
                    segments.append(segment)

    # sort segments
    segments.sort(key=lambda segments: segments.get("segment_id"))

    return segments


def flights_of_day(day):
    """
    Returns list of flights that took place at a certain day.
    """

    for mission in list(META):
        for platform in list(META[mission]):
            for flight_id in list(META[mission][platform]):
                flight = META[mission][platform][flight_id]
                if pd.Timestamp(flight["date"]) == pd.Timestamp(day):
                    yield flight_id


def day_of_flight(flight_id):
    """
    Returns list of flights that took place at a certain day.
    """

    return meta(flight_id)["date"]


# functions required to match remote sensing instruments from cologne
# once this list exists, I can better apply cloud masks to specific flights at
# high flight altitude
def get_all_flights(mission, platform):
    """
    Get research flights of a specific aircraft and mission.
    """

    if type(mission) == str:
        mission = [mission]

    if type(platform) == str:
        platform = [platform]

    flight_ids = [
        f
        for m in list(META)
        for p in list(META[m])
        for f in list(META[m][p])
        if m in list(mission)
        if p in list(platform)
    ]

    if "HALO-AC3_HALO_RF01" in flight_ids:
        flight_ids.remove("HALO-AC3_HALO_RF01")  # transfer flight

    if "HALO-AC3_HALO_RF00" in flight_ids:
        flight_ids.remove("HALO-AC3_HALO_RF00")  # test flight

    return flight_ids


def get_dropsonde_flight_ids():
    """
    Returns list of flights ids where dropsondes are available.
    """

    flight_ids = get_all_flights(
        mission=["ACLOUD", "AFLUX", "MOSAiC-ACA", "HALO-AC3"], platform="P5"
    )

    flight_ids.remove("ACLOUD_P5_RF04")
    flight_ids.remove("ACLOUD_P5_RF08")
    flight_ids.remove("ACLOUD_P5_RF15")
    flight_ids.remove("ACLOUD_P5_RF25")
    flight_ids.remove("AFLUX_P5_RF03")
    flight_ids.remove("AFLUX_P5_RF11")
    flight_ids.remove("AFLUX_P5_RF12")
    flight_ids.remove("AFLUX_P5_RF13")
    flight_ids.remove("AFLUX_P5_RF14")
    flight_ids.remove("HALO-AC3_P5_RF06")
    flight_ids.remove("MOSAiC-ACA_P5_RF02")
    flight_ids.remove("MOSAiC-ACA_P5_RF03")
    flight_ids.remove("MOSAiC-ACA_P5_RF04")

    return flight_ids


def get_amali_flight_ids(only_downward=False):
    """
    Returns list of all ac3airborne flight ids, where amali measured
    """

    flight_ids = get_all_flights(
        mission=["ACLOUD", "AFLUX", "MOSAiC-ACA", "HALO-AC3"], platform="P5"
    )

    flight_ids.remove("ACLOUD_P5_RF15")
    flight_ids.remove("AFLUX_P5_RF02")
    flight_ids.remove("MOSAiC-ACA_P5_RF02")
    flight_ids.remove("MOSAiC-ACA_P5_RF03")
    flight_ids.remove("MOSAiC-ACA_P5_RF09")  # laser off throughout the flight
    flight_ids.remove("HALO-AC3_P5_RF02")
    flight_ids.remove("HALO-AC3_P5_RF06")

    if only_downward:
        flight_ids.remove("ACLOUD_P5_RF10")

    return flight_ids


def get_mirac_a_flight_ids():
    """
    Returns list of all ac3airborne flight ids, where mirac-a measured.

    Note: this includes test flights that are not included in radar processing
    """

    flight_ids = get_all_flights(
        mission=["ACLOUD", "AFLUX", "MOSAiC-ACA", "HALO-AC3"], platform="P5"
    )

    flight_ids.remove("ACLOUD_P5_RF13")

    return flight_ids


def get_mirac_p_hatpro_flight_ids():
    """
    Returns list of all ac3airborne flight ids, where mirac-p/hatpro measured.
    """

    flight_ids = get_all_flights(
        mission=["ACLOUD", "AFLUX", "MOSAiC-ACA", "HALO-AC3"], platform="P5"
    )

    flight_ids.remove("MOSAiC-ACA_P5_RF03")

    return flight_ids
