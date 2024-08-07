"""
Read PAMTRA simulation along flight track based on ERA-5
"""

import os

import ac3airborne
import numpy as np
import xarray as xr

CAT = ac3airborne.get_intake_catalog()
META = ac3airborne.get_flight_segments()
PATH_CACHE_INTAKE = dict(
    storage_options={
        "simplecache": dict(
            cache_storage=os.environ["PATH_CACHE_INTAKE"],
            same_names=True,
        )
    }
)


def read_pamtra_era5(flight_id, frequency):
    """
    Read PAMTRA ERA-5 simulation along flight track
    """

    mission, platfo
    rm, name = flight_id.split("_")

    ds = xr.open_dataset(
        os.path.join(
            "/net/secaire/mech",
            "data/era5_pamtra/flights",
            f"ERA5_{flight_id}_passive.nc",
        )
    )["tb"].sel(frequencies=frequency)

    # remove dimensions (what is lev_2?)
    ds = ds.sel(grid_y=0).reset_coords(drop=True)

    # select only downward and transform angles
    ds = ds.sel(angles=slice(180, 90))
    ds["angles"] = 180 - ds["angles"]

    ds["polarizations"] = ["V", "H"]

    ds = ds.rename({"angles": "angle"})
    ds = ds.rename({"polarizations": "polarization"})
    ds = ds.rename({"outlevels": "obs_height"})
    ds = ds.rename({"time": "time_era5"})

    # time in pamtra is from gps_ins data on ac3airborne but not provided!
    ds_gps = (
        CAT[mission]["P5"]["GPS_INS"][flight_id]
        .to_dask()
        .sel(
            time=slice(
                META[mission]["P5"][flight_id]["takeoff"],
                META[mission]["P5"][flight_id]["landing"],
            )
        )
    )

    # remove duplicate times in gps data
    ds_gps = ds_gps.sel(time=~ds_gps.indexes["time"].duplicated())

    # drop where lon or lat is nan
    ds_gps = ds_gps.sel(time=(~np.isnan(ds_gps.lat)) | (~np.isnan(ds_gps.lon)))

    ds["time"] = ("time_era5", ds_gps.time.values)
    ds = ds.swap_dims({"time_era5": "time"})
    ds = ds.reset_coords()

    return ds
