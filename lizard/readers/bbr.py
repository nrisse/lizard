"""
Read broadband radiance and KT-19 from intake catalog
"""

import os

import ac3airborne
from dotenv import load_dotenv

load_dotenv()

META = ac3airborne.get_flight_segments()
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


def read_bbr(
    flight_id, reduce_to_flight=True, resample=True, attitude_flag=False
):
    """
    Read BBR for given research flight.
    """

    mission, platform, name = flight_id.split("_")

    if mission == "HALO-AC3":
        ds = CAT[mission][platform]["BROADBAND_IRRADIANCE"][flight_id](
            **PATH_CACHE_INTAKE, **CRED
        ).read()
    else:
        ds = CAT[mission][platform]["BROADBAND_IRRADIANCE"][flight_id](
            **PATH_CACHE_INTAKE
        ).read()

    if "Time" in list(ds.dims):
        ds["Time"] = ds.time
        ds = ds.drop("time")
        ds = ds.rename({"Time": "time"})

    if reduce_to_flight:
        ds = ds.sel(
            time=slice(
                META[mission][platform][flight_id]["takeoff"],
                META[mission][platform][flight_id]["landing"],
            )
        )

    if attitude_flag:
        ds = ds.sel(time=ds.Attitude_Flag == 0)

    # resample to 1 s resolution
    if resample:
        glob_attrs = ds.attrs
        var_attrs = {x: ds[x].attrs for x in list(ds)}
        coord_attrs = {x: ds[x].attrs for x in list(ds.coords)}
        ds = ds.to_pandas().resample("1S").mean().to_xarray()
        ds.attrs = glob_attrs

        for x, a in var_attrs.items():
            ds[x].attrs = a

        for x, a in coord_attrs.items():
            ds[x].attrs = a

    # KT-19 TB is in C for HALO-AC3 and in K for all other missions
    if mission == "HALO-AC3":
        print("Converting KT-19 TB from deg C to K")
        ds["KT19"] = ds["KT19"] + 273.15

    return ds
