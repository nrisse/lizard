"""
Reads GPS/INS data from ac3airborne intake catalog.
"""

import os

import ac3airborne
from dotenv import load_dotenv

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


def read_gps_ins(flight_id):
    """
    Read GPS/INS data for a specific flight. The heading convention of HALO
    and Polar 5 is matched here, using the Polar 5 convention for all
    aircraft. Read below for the exact conventions.

    Heading convention:
    - south: -180/180 degrees
    - east: 90 degrees
    - north: 0 degrees
    - west: -90 degrees

    Roll convention:
    - left wing up is positive, right wing up is negative (i.e. left turn has
      negative roll angle and right turn has positive roll angle)

    Pitch convention:
    - front up is positive, front down is negative (i.e. ascends have positive
      pitch angle and descents have negative pitch angle)

    Parameters
    ----------
    flight_id: ac3airborne flight id
    """

    mission, platform, name = flight_id.split("_")

    if mission == "HALO-AC3" and platform == "HALO":
        ds = CAT[mission][platform]["GPS_INS"][flight_id](
            **PATH_CACHE_INTAKE, **CRED
        ).read()
        ds = ds.rename({"yaw": "heading"})

        # same definition as for polar 5
        ds["heading"] *= -1
        ds["heading"] += 90
        ds["heading"][ds["heading"] > 180] -= 360

    else:
        ds = CAT[mission][platform]["GPS_INS"][flight_id](
            **PATH_CACHE_INTAKE
        ).read()

    return ds
