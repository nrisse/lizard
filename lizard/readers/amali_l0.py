"""
Read AMALi data from local intake catalog
"""

import os

import ac3airborne
import intake

META = ac3airborne.get_flight_segments()
CAT = intake.open_catalog(
    os.path.join(os.environ["PATH_DAT"], "obs/campaigns/intake/catalog.yaml")
)
os.environ["LOCAL_DATA"] = "/data/obs/campaigns/"
PATH_CACHE_INTAKE = dict(
    storage_options={
        "simplecache": dict(
            cache_storage=os.environ["PATH_CACHE_INTAKE"],
            same_names=True,
        )
    }
)


def read_amali(flight_id):
    """
    Reads AMALi L0 data from local intake catalog
    """

    mission, platform, name = flight_id.split("_")
    flight = META[mission][platform][flight_id]

    ds = CAT[mission][platform]["AMALi"][flight_id](**PATH_CACHE_INTAKE).read()

    ds = ds.sel(time=slice(flight["takeoff"], flight["landing"]))

    ds = ds.rename({"height": "range"})

    return ds
