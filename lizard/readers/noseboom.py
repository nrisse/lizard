"""
Read noseboom measurements from Polar 5.

The following variables are available on PANGAEA:
ACLOUD 1s (this is in intake)
UTC    h   lon   lat  p     gs  pitch   roll     rh      T      u      v    tas

ACLOUD turbdata (this is in intake)
t  lon         lat       h      p      T      u      v   w  pitch   roll thdg

AFLUX turbdata (this is in intake)
t  lon         lat       h      p      T      u      v   w  pitch   roll thdg

MOSAiC-ACA 100 Hz (this is in intake)
UTC    h   lon   lat  p     gs  pitch   roll     rh      T      u      v    tas

--> AFLUX does not contain RH!!! Therefore, use a local file for AFLUX:
AFLUX 1s (from Christoph Luepkes):
UTC    h   lon   lat  p     gs  pitch   roll     rh      T      u      v    tas
... until PANGAEA is updated
"""

import os

import ac3airborne
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

META = ac3airborne.get_flight_segments()
CAT = ac3airborne.get_intake_catalog()
INTAKE_CACHE = dict(
    storage_options={
        "simplecache": dict(
            cache_storage=os.environ["INTAKE_CACHE"],
            same_names=True,
        )
    }
)


def read_noseboom(flight_id):
    """
    Read noseboom data from intake

    Parameters
    ----------
    flight_id: ac3airborne flight id
    """

    mission, platform, name = flight_id.split("_")
    flight = META[mission][platform][flight_id]

    if mission in ["ACLOUD", "AFLUX"]:
        print("WARNING: Using file from local server instead of intake.")

        if flight_id == "AFLUX_P5_RF02":
            print(f"No data for {flight_id}")
            return None

        date_path = flight["date"].strftime("%Y/%m/%d")
        date = flight["date"].strftime("%Y%m%d")

        df = pd.read_fwf(
            os.path.join(
                os.environ["PATH_DAT"],
                f"obs/campaigns/{mission.lower()}/p5/noseboom/{date_path}",
                f"Flight_{date}_{name[2:]}_P5_1s.asc",
            ),
            comment="!",
            infer_nrows=50000,
        )

        df = df.rename(columns={"UTC": "t"})

    elif mission == "HALO-AC3":
        print(f"No data for {flight_id}")
        return None

    else:
        df = CAT[mission][platform]["NOSE_BOOM"][flight_id](
            **INTAKE_CACHE
        ).read()

    df["t"] = pd.to_datetime(
        df["t"], unit="s", origin=META[mission][platform][flight_id]["date"]
    )
    ds = df.set_index("t").to_xarray()
    ds = ds.rename({"t": "time"})

    # reduce to flight time
    ds = ds.sel(time=slice(flight["takeoff"], flight["landing"]))

    return ds
