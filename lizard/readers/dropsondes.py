"""
Read all dropsondes of research flight
"""

import os

import ac3airborne
import numpy as np

ac3cloud_username = os.environ["AC3_USER"]
ac3cloud_password = os.environ["AC3_PASSWORD"]

credentials = dict(user=ac3cloud_username, password=ac3cloud_password)

# local caching
kwds = {
    "simplecache": dict(
        cache_storage=os.environ["INTAKE_CACHE"], same_names=True
    )
}

cat = ac3airborne.get_intake_catalog()
meta = ac3airborne.get_flight_segments()


def read_dropsonde(flight_id):
    """
    Read all dropsondes of research flight
    """

    mission, platform, name = flight_id.split("_")
    cat_ds = cat[mission][platform]["DROPSONDES"][flight_id]

    dict_dsd = {}
    if mission in ["ACLOUD", "AFLUX", "MOSAiC-ACA"]:
        try:
            for i in range(1, 100):
                dict_dsd[f"{flight_id}_{str(i).zfill(2)}"] = cat_ds(
                    i_sonde=i, storage_options=kwds
                ).read()
        except OSError:
            pass

    elif mission == "HALO-AC3":
        times = cat_ds.description.split(",")

        for i, t in enumerate(times, start=1):
            dict_dsd[f"{flight_id}_{str(i).zfill(2)}"] = cat_ds(
                time=t, storage_options=kwds, **credentials
            ).read()

    # add launch time
    if mission in ["ACLOUD", "AFLUX", "MOSAiC-ACA"]:
        for k in dict_dsd.keys():
            dict_dsd[k] = add_launch_time(dict_dsd[k], flight_id)

            # convert time from decimal hours to actual date format
            dict_dsd[k]["Time"] = dict_dsd[k].Time.astype(
                "timedelta64[h]"
            ) + np.datetime64(meta[mission][platform][flight_id]["date"])

            # set time as index and remove z (which just counts from 0 to number of values)
            dict_dsd[k] = dict_dsd[k].assign_coords(z=dict_dsd[k].Time.values)
            dict_dsd[k] = dict_dsd[k].drop("Time")
            dict_dsd[k] = dict_dsd[k].rename({"z": "Time"})

    elif mission == "HALO-AC3":
        for k in dict_dsd.keys():
            if platform == "P5":
                dict_dsd[k] = dict_dsd[k].rename({"base_time": "launch_time"})

    return dict_dsd


def add_launch_time(ds, flight_id):
    """
    Add launch time as variable to dropsonde
    """

    mission, platform, name = flight_id.split("_")
    flight = meta[mission][platform][flight_id]

    ts = ds.attrs["Launch_Time_UTC"].split(":")
    ms = ["h", "m", "s"]
    x = np.array([np.timedelta64(int(t), m) for t, m in zip(ts, ms)]).sum()
    ds["launch_time"] = np.datetime64(flight["date"]) + x

    return ds
