"""
Read HAMP cloud mask
"""

import xarray as xr
import os
from dotenv import load_dotenv

load_dotenv()


def read_cloudmask():
    """
    Reads cloud mask derived from HAMP for entire campaign

    Returns
    -------
    ds: hamp cloud mask
    """

    ds = xr.open_dataset(os.path.join(
        os.environ['PATH_SEC'],
        'hamp_cloud_mask.nc'
    ))

    return ds
