"""
Reads pre-calculated mean AMSR2 sea ice concentration for airborne field
campaign.
"""

import os

import xarray as xr
from dotenv import load_dotenv

load_dotenv()


def read_mean_sea_ice(mission):
    """
    Read mean sea ice concentration for campaign period.

    Parameters
    -------
    mission: name of field campaign

    Returns
    -------
    xr.Dataset with mean sea ice concentration.
    """

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_DAT"],
            "obs/campaigns",
            mission.lower(),
            "auxiliary/sea_ice/avg",
            f"{mission}_mean_sic_asi-AMSR2-n6250-v5.4.nc",
        )
    )

    return ds
