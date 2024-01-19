"""
Read cloud top height from intake catalog
"""

import os

import ac3airborne

CAT = ac3airborne.get_intake_catalog()
INTAKE_CACHE = dict(
    storage_options={
        "simplecache": dict(
            cache_storage=os.environ["INTAKE_CACHE"],
            same_names=True,
        )
    }
)


def read_cloud_top_height(flight_id):
    """
    Read MiRAC-A for given research flight.
    """

    mission, platform, name = flight_id.split("_")

    ds = CAT[mission][platform]["CLOUD_TOP_HEIGHT"][flight_id](
        **INTAKE_CACHE
    ).read()

    return ds
