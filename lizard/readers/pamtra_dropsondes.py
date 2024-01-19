"""
Read PAMTRA dropsonde simulations prepared by Mario
"""

import os
from glob import glob

import xarray as xr


def read_pamtra_dropsondes(sonde_id):
    """
    Read PAMTRA simulation of dropsondes and ERA-5 above
    """

    ds = xr.open_dataset(
        os.path.join(
            "/net/secaire/mech", "data/lwp_project/", f"pamtra_{sonde_id}.nc"
        )
    )

    # select clear-sky sondes
    ds = ds.sel(grid_y=0)
    ds = ds.sel(grid_x=ds.cwp == 0).sel(grid_x=0)  # different lwp heights

    # select only downward and transform angles
    ds = ds.sel(angles=slice(180, 90))
    ds["angles"] = 180 - ds["angles"]

    ds["passive_polarisation"] = ["V", "H"]

    ds = ds.rename({"angles": "angle"})
    ds = ds.rename({"passive_polarisation": "polarization"})

    ds["outlevel"] = ds["outlevels"]
    ds = ds.drop_vars("outlevels")
    ds = ds.rename({"outlevel": "obs_height"})

    return ds


def read_pamtra_dropsondes_from_flight_id(flight_id):
    """
    Read all sondes from flight id
    """

    files = sorted(
        glob(
            os.path.join(
                "/net/secaire/mech",
                "data/lwp_project/",
                f"pamtra_{flight_id}_*.nc",
            )
        )
    )

    dct_ds_pam = {}
    for file in files:
        sonde_id = flight_id + file.split(flight_id)[-1][:3]
        dct_ds_pam[sonde_id] = read_pamtra_dropsondes(sonde_id)

    return dct_ds_pam
