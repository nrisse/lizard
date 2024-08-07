"""
Read HAMP MIRA radar reflectivity
"""

import os

import ac3airborne
import numpy as np
import xarray as xr
from scipy.interpolate import interp1d

from lizard.ac3airlib import get_all_flights, meta
from lizard.readers.gps_ins import read_gps_ins

CAT = ac3airborne.get_intake_catalog()

CRED = dict(user=os.environ["AC3_USER"], password=os.environ["AC3_PASSWORD"])

kwds = {
    "simplecache": dict(
        cache_storage=os.environ["PATH_CACHE_INTAKE"], same_names=True
    )
}


def read_all():
    """
    Read all HAMP MIRA observations into a single dask array

    Returns
    -------
    ds: dask array with all hamp tbs
    """

    flight_ids = get_all_flights("HALO-AC3", "HALO")
    flight_ids.remove("HALO-AC3_HALO_RF00")

    lst_ds = []
    for flight_id in flight_ids:
        ds = read_mira(flight_id)
        ds = ds.chunk({"time": 5000})
        lst_ds.append(ds)

    ds = xr.concat(lst_ds, dim="time")

    return ds


def read_mira(flight_id):
    """
    Read MIRA data onboard of HALO aircraft

    Parameters
    ----------
    flight_id: ac3airborne flight id

    Returns
    -------
    ds: mira data interpolated onto regular height grid
    """

    mission, platform, name = flight_id.split("_")
    ds = CAT[mission][platform]["HAMP_RADAR"][flight_id](
        storage_options=kwds, **CRED
    ).read()

    # set values with -888 to nan
    variables = ["dBZg", "Zg", "Ze", "dBZe", "LDRg", "RMSg", "VELg", "SNRg"]
    ds[variables] = ds[variables].where(ds[variables] != -888)

    return ds


def height_grid(da_ze, flight_id):
    """
    Interpolate signal on regular height grid (no curves considered)

    Parameters
    ----------
    da_ze: data array with radar reflectivity in dBZ
    flight_id: ac3airborne flight id

    Returns
    -------
    ds: dataset interpolate onto regular height grid of 30 m (original res)
    """

    # read gps data
    ds_gps = read_gps_ins(flight_id)

    # match gps and radar data
    ds_gps, da_ze = xr.align(ds_gps, da_ze)

    # interpolate radar reflectivity onto regular height grid
    height_sig = (ds_gps.alt - da_ze.range).values  # (time, range)
    height = np.arange(-200, 14001, 30)  # (height)
    ze = 10 ** (0.1 * da_ze.values)  # (time, range)
    ze_reg = np.full((ze.shape[0], height.shape[0]), fill_value=np.nan)
    for j in range(ze.shape[0]):
        f = interp1d(
            height_sig[j, :],
            ze[j, :],
            fill_value=np.nan,
            kind="linear",
            bounds_error=False,
        )
        ze_reg[j, :] = f(height)

    # back to dbz
    ze_reg = 10 * np.log10(ze_reg)

    ds = xr.Dataset()
    ds.coords["height"] = height
    ds.coords["time"] = da_ze.time
    ds["ze"] = (("time", "height"), ze_reg)

    return ds
