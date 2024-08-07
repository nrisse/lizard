"""
Read HALO KT-19 from intake.
"""

import os

import ac3airborne

CAT = ac3airborne.get_intake_catalog()

CRED = dict(user=os.environ["AC3_USER"], password=os.environ["AC3_PASSWORD"])

kwds = {
    "simplecache": dict(
        cache_storage=os.environ["PATH_CACHE_INTAKE"], same_names=True
    )
}


def read_halo_kt19(flight_id):
    """
    Reads HALO KT-19 measurements from intake. The internal temperature
    variable (temp_KT19) is dropped to avoid confusion with Polar 5 naming
    convention.

    Parameters
    ----------
    flight_id: ac3airborne flight id

    Returns
    -------
    ds: xarray Dataset with KT-19 IR temperature
    """

    mission, platform, name = flight_id.split("_")

    ds = CAT[mission][platform]["KT19"][flight_id](
        storage_options=kwds, **CRED
    ).read()

    ds = ds.drop(["temp_KT19", "emis"])
    ds = ds.rename({"temp_bright": "KT19"})

    return ds
