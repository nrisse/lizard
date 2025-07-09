"""
Read HAMP Tbs from intake.
"""

import os

import ac3airborne
import numpy as np
import pandas as pd
import xarray as xr

from lizard.ac3airlib import day_of_flight, get_all_flights

CAT = ac3airborne.get_intake_catalog()

CRED = dict(user=os.environ["AC3_USER"], password=os.environ["AC3_PASSWORD"])


def read_hamp_uncorrected(flight_id):
    """
    Reads processed HAMP Tbs from ac3airborne intake catalog and performs
    some conversions of the data format. The conversions ensure the same
    variable names as for MiRAC/HATPRO onboard of Polar 5.

    The parameters that are naturally provided are dropped:
    - surface_mask
    - interpolate_flag

    Parameters
    ----------
    flight_id: ac3airborne flight id

    Returns
    -------
    ds: xarray Dataset with HAMP Tbs
    """

    mission, platform, name = flight_id.split("_")

    date = day_of_flight(flight_id).strftime("%Y%m%d")
    ds = xr.open_dataset(
        os.path.join(
            "/data/obs/campaigns/halo-ac3/halo/hamp/uncorrected/",
            f"HALO-AC3_HALO_hamp_radiometer_{date}_{name}.nc",
        )
    )

    # times where any channel is interpolated are removed
    ds = ds.sel(time=~(ds.interpolate_flag == 1).any("uniRadiometer_freq"))

    ds = ds.drop(["freq", "surface_mask", "interpolate_flag"])
    ds = ds.rename({"uniRadiometer_freq": "frequency", "TB": "tb"})

    # apply calibration
    ds = apply_calibration(ds, flight_id)

    # channel order as expected by the filter files
    ds["channel"] = (
        "frequency",
        np.array(
            [
                20,
                21,
                22,
                23,
                24,
                25,
                15,
                16,
                17,
                18,
                19,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
            ]
        ),
    )
    ds = ds.swap_dims({"frequency": "channel"})
    ds = ds.reset_coords()
    ds = ds.sel(channel=np.sort(ds.channel))

    return ds


def read_hamp(flight_id):
    """
    Reads processed HAMP Tbs from ac3airborne intake catalog and performs
    some conversions of the data format. The conversions ensure the same
    variable names as for MiRAC/HATPRO onboard of Polar 5.

    The parameters that are naturally provided are dropped:
    - surface_mask
    - interpolate_flag

    Parameters
    ----------
    flight_id: ac3airborne flight id

    Returns
    -------
    ds: xarray Dataset with HAMP Tbs
    """

    mission, platform, name = flight_id.split("_")

    date = day_of_flight(flight_id).strftime("%Y%m%d")
    ds = xr.open_dataset(
        os.path.join(
            "/data/obs/campaigns/halo-ac3/halo/hamp/unified_v2.7",
            f"HALO_HALO_AC3_radiometer_unified_{name}_{date}_v2.7.nc",
        )
    )

    # times where any channel is interpolated are removed
    ds = ds.sel(time=~(ds.interpolate_flag == 1).any("uniRadiometer_freq"))

    ds = ds.rename({"uniRadiometer_freq": "frequency", "TB": "tb"})

    ds["channel"] = ("frequency", np.arange(1, len(ds.frequency) + 1))
    ds = ds.swap_dims({"frequency": "channel"})
    ds = ds.reset_coords()

    ds = ds.drop(["freq", "frequency", "surface_mask", "interpolate_flag"])

    # correction for 30 March 2022
    if flight_id == "HALO-AC3_HALO_RF11":
        ds_calib = read_calibration(flight_id, version="v2023.04").isel(date=0).reset_coords(drop=True)

        ds_calib["channel"] = ("freq", np.arange(1, 26))
        ds_calib = ds_calib.swap_dims({"freq": "channel"})
        ds_calib = ds_calib.reset_coords()

        # undo slope and offset calibration
        ds["tb"] = (ds["tb"] - ds_calib["offset"]) / ds_calib["slope"]

        # apply bias correction
        ds["tb"] = ds["tb"] - ds_calib["bias"]

    return ds


def read_hamp_all():
    """
    Read all HAMP observations into a single dask array

    Returns
    -------
    ds: dask array with all hamp tbs
    """

    flight_ids = get_all_flights("HALO-AC3", "HALO")
    flight_ids.remove("HALO-AC3_HALO_RF00")

    lst_ds = []
    for flight_id in flight_ids:
        ds = read_hamp(flight_id)
        ds = ds.chunk({"time": 100000})
        lst_ds.append(ds)

    ds = xr.concat(lst_ds, dim="time", data_vars=["tb"])

    return ds


def read_calibration(flight_id, version="v2024.01"):
    date_str = day_of_flight(flight_id).strftime("%Y%m%d")
    ds = xr.open_dataset(
        os.path.join(
            "/data/obs/campaigns/halo-ac3/halo/hamp/cssc",
            version,
            f"HALO-AC3_HALO_HAMP_TB_offset_correction_{date_str}.nc",
        )
    )
    return ds


def apply_calibration(ds, flight_id):
    """
    This adds the calibration offset to HAMP

    corrected_tb = slope * tb + offset
    """

    ds_calib = read_calibration(flight_id)

    slope = ds_calib["slope"].sel(freq=ds["frequency"], date=date_str)
    offset = ds_calib["offset"].sel(freq=ds["frequency"], date=date_str)

    ds["tb"] = slope * ds["tb"] + offset

    return ds


def read_hamp_separate():
    """
    Reader for separate HAMP channels
    """

    flight = None
    ds1 = None
    ds2 = None
    ds3 = None

    # frequencies
    freqs = np.concatenate([ds1.Freq.values, ds2.Freq.values, ds3.Freq.values])

    # time
    times = pd.date_range(flight["takeoff"], flight["landing"], freq="250ms")

    # make sure, that sampling interval is constant
    _, ix = np.unique(ds1.time, return_index=True)
    assert (ix[1:] - ix[:-1] != 4).sum() == 0

    _, ix = np.unique(ds2.time, return_index=True)
    assert (ix[1:] - ix[:-1] != 4).sum() == 0

    _, ix = np.unique(ds3.time, return_index=True)
    assert (ix[1:] - ix[:-1] != 4).sum() == 0

    # sampling interval is 0.25 s, but this is not in the time stamp
    # therefore modify the time stamp
    dt = np.array([np.timedelta64(t, "ms") for t in [0, 250, 500, 750]])

    dt1 = np.tile(dt, int(len(ds1.time) / 4))
    ds1["time"] = ds1["time"] + dt1

    dt2 = np.tile(dt, int(len(ds2.time) / 4))
    ds2["time"] = ds2["time"] + dt2

    dt3 = np.tile(dt, int(len(ds3.time) / 4))
    ds3["time"] = ds3["time"] + dt3

    # reindex
    ds1 = ds1.reindex({"time": times})
    ds2 = ds2.reindex({"time": times})
    ds3 = ds3.reindex({"time": times})

    # generate a tb array
    tb = np.concatenate(
        [ds1.TBs.values, ds2.TBs.values, ds3.TBs.values], axis=1
    )

    # rewrite in new format
    ds = xr.Dataset()
    ds.coords["time"] = times
    ds.coords["channel"] = np.arange(1, len(freqs) + 1)
    ds["frequency"] = ("channel", freqs)
    ds["tb"] = (("time", "channel"), tb)

    return ds
