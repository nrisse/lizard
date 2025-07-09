"""
Reads AMSR2 sea ice concentration along flight track
"""

import os

import ac3airborne
import xarray as xr
from dotenv import load_dotenv

from lizard.ac3airlib import get_all_flights

load_dotenv()

CAT = ac3airborne.get_intake_catalog()
PATH_CACHE_INTAKE = dict(
    storage_options={
        "simplecache": dict(
            cache_storage=os.environ["PATH_CACHE_INTAKE"],
            same_names=True,
        )
    }
)


def read_amsr2_sic_track(flight_id):
    """
    Read brightness temperature dataset file.

    Parameters
    ----------
    flight_id: research flight id from ac3airborne.
    """

    mission, platform, name = flight_id.split("_")

    ds = CAT[mission][platform]["AMSR2_SIC"][flight_id](**PATH_CACHE_INTAKE).read()

    return ds


def read_amsr2_sic_track_all():
    """
    Read AMSR2 sea ice concentration extracted along flight track.
    then combines all flights into a single dask array. By this, one avoids
    using loops to filter all TB data for sea ice for example.

    Returns
    -------
    ds: dask array with all hamp tbs
    """

    flight_ids = get_all_flights("HALO-AC3", "HALO")

    lst_ds = []
    for flight_id in flight_ids:
        ds = read_amsr2_sic_track(flight_id)
        ds = ds.chunk({"time": 10000})
        lst_ds.append(ds)

    ds = xr.concat(lst_ds, dim="time")

    # convert longitude format
    ds["lon"].loc[{"time": ds["lon"] > 180}] -= 360

    return ds
