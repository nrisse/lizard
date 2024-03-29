"""
Read file with brightness temperatures and footprint positions.
"""

import os
import xarray as xr
import ac3airborne
from dotenv import load_dotenv

load_dotenv()

META = ac3airborne.get_flight_segments()


def read_tb(flight_id):
    """
    Read brightness temperature dataset file.

    Parameters
    ----------
    flight_id: research flight id from ac3airborne.
    """

    mission, platform, name = flight_id.split('_')
    date = META[mission][platform][flight_id]['date'].strftime('%Y%m%d')

    ds = xr.open_dataset(os.path.join(
        os.environ['PATH_SEC'],
        "data/sea_ice_emissivity/"
        'brightness_temperature',
        f'tb_{flight_id}_{date}.nc'))

    return ds
