"""
Read MiRAC-A from intake catalog
"""

import os

import ac3airborne
import xarray as xr
from dotenv import load_dotenv

from lizard.ac3airlib import day_of_flight

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
CRED = dict(user=os.environ["AC3_USER"], password=os.environ["AC3_PASSWORD"])


def read_mirac_a(flight_id, offline=True, **xarray_kwargs):
    """
    Read MiRAC-A for given research flight.
    """

    mission, platform, name = flight_id.split("_")
    date = day_of_flight(flight_id)

    if offline:
        ds = xr.open_dataset(
            os.path.join(
                "/data/obs/campaigns",
                mission.lower(),
                "p5/mirac_radar/compact",
                f"{mission}_P5_MiRAC-A_{date.strftime('%Y%m%d')}_{name}.nc",
            )
        )

        return ds

    else:
        try:
            if mission == "HALO-AC3":
                ds = CAT[mission][platform]["MiRAC-A"][flight_id](
                    **PATH_CACHE_INTAKE, **CRED, xarray_kwargs=xarray_kwargs
                ).read()
            else:
                ds = CAT[mission][platform]["MiRAC-A"][flight_id](
                    **PATH_CACHE_INTAKE, xarray_kwargs=xarray_kwargs
                ).read()

            return ds

        except KeyError:
            # flights without public mirac-a data or failed instrument
            assert flight_id in [
                "HALO-AC3_P5_RF02",
                "ACLOUD_P5_RF13",
                "HALO-AC3_P5_RF06",
            ]

            return None


def read_mirac_a_tb(flight_id):
    ds = read_mirac_a(
        flight_id,
        drop_variables=[
            "Ze",
            "Ze_flag",
            "Ze_unfiltered",
            "height",
            "lon",
            "lat",
            "alt",
        ],
    )

    if ds is not None:
        ds = ds.expand_dims({"channel": [1]}, axis=-1)

    return ds
