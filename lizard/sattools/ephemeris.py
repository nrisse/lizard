"""
Calculate sub-satellite point from daily ephemeris data using skyfield module.
This library uses the SGP4 orbital propagation model, on which the TLE files
are based.

Input data
ephemeris data (TLE): describes state of Earth-orbiting element
see also documentation https://www.space-track.org/documentation#tle
downloaded from https://www.space-track.org as json files for the five mission
periods. All satellites are contained in one json file and are filtered later.

Documentation: https://rhodesmill.org/skyfield/earth-satellites.html

Execution time: When running for 10 months with 10 second resolution, it takes
about 2 minutes per satellite. The performance is limited by the skyfield
calculations and may be improved by neglecting some TLE files, the question is
by how much the satellite would differ, if we calculate the position with a
TLE file from a few days back instead of a few hours. To remain accurate here,
I would not neglect files.


    # provide the upper functionality as a class, so that you can recalculate
    # satellite positions for given input times if needed!
    # then also make sure, that the database is maybe much longer for these
    # satellites :) not just campaign periods
    
TODO: get jason files a bit before the campaign period, so that it is always
earlier than the first time step I want to analyze!
"""


import json
import os
from glob import glob

import numpy as np
import pandas as pd
import xarray as xr
from dotenv import load_dotenv
from skyfield.api import EarthSatellite, load, wgs84

load_dotenv()


# norad id of satellites
sat_dct = {
    "Aqua": "27424",
    "Metop-A": "29499",
    "Metop-B": "38771",
    "Metop-C": "43689",
    "NOAA-15": "25338",
    "NOAA-18": "28654",
    "NOAA-19": "33591",
    "NOAA-20": "43013",
    "SNPP": "37849",
    "GCOM-W": "38337",
    "DMSP-F15": "25991",
    "DMSP-F16": "28054",
    "DMSP-F17": "29522",
    "DMSP-F18": "35951",
}


if __name__ == "__main__":
    # request data from space-track.org based on this
    # requested for two-monthly mission periods for all satellites
    # there might also be an api soon
    for x in sat_dct.keys():
        print(",", x)

    print([int(x) for x in sat_dct.values()])

    # create time for all missions
    times1 = pd.date_range("2017-05-01", "2017-06-30", freq="10s")
    times2 = pd.date_range("2019-03-01", "2019-04-30", freq="10s")
    times3 = pd.date_range("2020-08-01", "2020-09-30", freq="10s")
    times4 = pd.date_range("2022-03-01", "2022-04-30", freq="10s")
    times5 = pd.date_range("2022-07-01", "2022-08-31", freq="10s")

    times = pd.to_datetime(
        np.concatenate([times1, times2, times3, times4, times5])
    )

    # %% read all tle files
    files = glob(
        os.path.join(os.environ["PATH_SAT"], "ephemeris/tle_multisat_*.json")
    )

    tle = []
    for file in files:
        with open(file, "r") as f:
            tle += json.load(f)

    # %% calculate satellite position for every time step
    ts = load.timescale()

    # output arrays
    arr_lat = np.full((len(times), len(sat_dct)), fill_value=np.nan)
    arr_lon = np.full((len(times), len(sat_dct)), fill_value=np.nan)
    arr_dt = np.full((len(times), len(sat_dct)), fill_value=np.nan)

    for i_sat, (sat_name, sat_id) in enumerate(sat_dct.items()):
        print(sat_name)

        # get subset of tle for the current satellite
        tle_sat = [t for t in tle if t["NORAD_CAT_ID"] == sat_id]
        tle_epochs = pd.to_datetime([x["EPOCH"] for x in tle_sat])

        # sort tle_sat by epoch time
        ix = np.argsort(tle_epochs)
        tle_sat = [tle_sat[i] for i in ix]
        tle_epochs = [tle_epochs[i] for i in ix]

        # indicates to which tle file the time belongs to
        i_tle = np.searchsorted(tle_epochs, times) - 1

        # create all individual satellite objects
        i_tle_unique = np.unique(i_tle)
        i_tle_unique = i_tle_unique[i_tle_unique != -1]

        # create satellite objects
        earth_sats = {
            i: EarthSatellite(tle_sat[i]["TLE_LINE1"], tle_sat[i]["TLE_LINE2"])
            for i in i_tle_unique
        }

        # predict locations for each satellite object
        for i, satellite in earth_sats.items():
            # get times belonging to the satellite tle position
            t = ts.utc(
                list(times[i_tle == i].year),
                list(times[i_tle == i].month),
                list(times[i_tle == i].day),
                list(times[i_tle == i].hour),
                list(times[i_tle == i].minute),
                list(times[i_tle == i].second),
            )

            geocentric = satellite.at(t)
            position = wgs84.subpoint_of(geocentric)

            # write output arrays
            arr_lat[i_tle == i, i_sat] = position.latitude.degrees
            arr_lon[i_tle == i, i_sat] = position.longitude.degrees
            arr_dt[i_tle == i, i_sat] = t - satellite.epoch  # in days

    # %% write output of satellite footprints positions for all satellites
    ds_sat = xr.Dataset()
    ds_sat.coords["time"] = times
    ds_sat.coords["sat"] = list(sat_dct.keys())
    ds_sat["sat_id"] = (("sat"), list(sat_dct.values()))
    ds_sat["lat"] = (("time", "sat"), arr_lat)
    ds_sat["lon"] = (("time", "sat"), arr_lon)
    ds_sat["dt"] = (("time", "sat"), arr_dt)

    # quality check
    ds_sat["lon"] = ds_sat.lon.where(ds_sat.dt < 5)
    ds_sat["lat"] = ds_sat.lat.where(ds_sat.dt < 5)
    ds_sat["dt"] = ds_sat.dt.where(ds_sat.dt < 5)

    assert (ds_sat.dt.min("time") > 0).all()

    # add attributes
    ds_sat["sat"].attrs = dict(description="Satellite name")

    ds_sat["sat_id"].attrs = dict(description="Satellite catalog number")

    ds_sat["lat"].attrs = dict(
        long_name="latitude", description="Sub-satellite latitude"
    )

    ds_sat["lon"].attrs = dict(
        long_name="longitude", description="Sub-satellite lonitude"
    )

    ds_sat["dt"].attrs = dict(
        long_name="time_difference",
        description="Time difference to TLE",
        units="days",
    )

    ds_sat.attrs = dict(
        title="Sub-satellite position",
        description="Sub-satellite positions from several satellite during"
        + "mission periods every 10 seconds based on TLE files",
        satellites=", ".join(sat_dct.keys()),
        author="Nils Risse",
        history=f'Created with tools/ephemeris.py on {np.datetime64("now")}',
    )

    # write to file
    ds_sat.to_netcdf(
        os.path.join(os.environ["PATH_SAT"], "tracks/sat_tracks.nc")
    )
