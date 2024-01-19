"""
Calculate co-location statistics based on sub-satellite coordinates from
different meteorological satellites.
"""


import os

import ac3airborne
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from cartopy.feature.nightshade import Nightshade
from dotenv import load_dotenv
from mw_satellites import sat_colors
from sat_tools import OSCAR

plt.ion()
load_dotenv()


def haversine(lon1, lat1, lon2=0, lat2=80):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)

    All args must be of equal length.
    """

    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    )

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c

    return km


if __name__ == "__main__":
    # read track data
    ds_sat = xr.open_dataset(
        os.path.join(os.environ["PATH_SAT"], "tracks/sat_tracks.nc")
    )

    # %% read oscar list
    osc = OSCAR()

    osc.only_passive()
    osc.only_space_agencies(osc.space_agencies)
    osc.only_sunsync()
    osc.no_limb()
    osc.drop_instruments()

    fre = osc.within_available(
        np.datetime64("2017-01-01"), np.datetime64("2022-08-30")
    )

    fre.satellite.unique()

    len(fre.satellite.unique())

    dct1 = osc.payload_of_satellites(fre.satellite.unique())
    dct2 = osc.satellites_of_instrument(fre.service.unique())

    # %% visualization on mercator projection
    t0 = np.datetime64("2019-04-11 12:10:00")
    t1 = np.datetime64("2019-04-11 12:40:00")

    fig, ax = plt.subplots(
        1, 1, subplot_kw=dict(projection=ccrs.PlateCarree())
    )

    ax.set_title(f"Satellite position every 10 seconds ({t0} - {t1})")

    ax.coastlines()
    ax.stock_img()
    ax.add_feature(Nightshade(t1.item(), alpha=0.2))

    t = dict(time=slice(t0, t1))

    for sat in ds_sat.sat.values:
        # annotate name at end position
        ax.annotate(
            sat,
            xy=(
                ds_sat.lon.sel(sat=sat, time=t1).item(),
                ds_sat.lat.sel(sat=sat, time=t1).item(),
            ),
            xycoords=ccrs.PlateCarree()._as_mpl_transform(ax),
        )

        ax.scatter(
            ds_sat.lon.sel(sat=sat, **t),
            ds_sat.lat.sel(sat=sat, **t),
            marker=".",
            label=sat,
            transform=ccrs.PlateCarree(),
        )

    ax.legend()

    # %% flight track statistics
    # define area of interest

    lon, lat = [0, 80]

    ds_sat["dist"] = xr.apply_ufunc(
        haversine,
        ds_sat["lon"],
        ds_sat["lat"],
        kwargs=dict(lon2=lon, lat2=lat),
    )

    ds_sat_dist_h_min = ds_sat["dist"].groupby("time.hour").min("time")

    # %%
    fig, axes = plt.subplots(
        2, 7, sharex=True, sharey=True, constrained_layout=True
    )

    for i, sat in enumerate(ds_sat.sat.values):
        ax = axes.flatten()[i]

        ax.set_title(sat)

        ax.plot(
            ds_sat_dist_h_min.hour,
            ds_sat_dist_h_min.sel(sat=sat),
            color="k",
        )

        ax.axvspan(6, 15, alpha=0.5)

    ax.set_ylim(bottom=0)
    ax.set_xlim(0, 23)

    axes[1, 0].set_xlabel("Hour [UTC]")
    axes[1, 0].set_ylabel("min(dist(sat, 80N, 0E)) [km]")

    # %% visualization of co-location with polar5
    meta = ac3airborne.get_flight_segments()
    cat = ac3airborne.get_intake_catalog()

    # all flights
    flights = [
        (mission, platform, flight_id)
        for mission in list(meta)
        if mission in ["ACLOUD", "AFLUX", "MOSAiC-ACA"]
        for platform in list(meta[mission])
        if platform in ["P5"]
        for flight_id in list(meta[mission][platform])
        if flight_id in ["AFLUX_P5_RF08"]
    ]

    # all flight segments
    flight_segments = {
        segment["segment_id"]: {**segment, "flight_id": flight_id}
        for mission in list(meta)
        for platform in list(meta[mission])
        if platform in ["P5"]
        for flight_id in list(meta[mission][platform])
        for segment in meta[mission][platform][flight_id]["segments"]
        if "segment_id" in segment.keys()
    }

    for mission, platform, flight_id in flights:
        flight = meta[mission][platform][flight_id]

        # read gps data
        ds_gps = cat[mission][platform]["GPS_INS"][flight_id].read()

        # get satellite positions during flight times
        t0 = flight_segments["AFLUX_P5_RF08_hl02"]["start"]
        t1 = flight_segments["AFLUX_P5_RF08_hl02"]["end"]
        # flight['takeoff'], flight['landing']

        ds_sat_flight = ds_sat.sel(time=slice(t0, t1))

        # calculate closest distance to 80N, and then look at thcases
        fig, ax = plt.subplots(
            1,
            1,
            subplot_kw=dict(projection=ccrs.NorthPolarStereo()),
            constrained_layout=True,
        )

        ax.coastlines()

        ax.set_extent([-10, 20, 77, 83])

        # plot gps track
        ax.scatter(
            ds_gps.lon,
            ds_gps.lat,
            transform=ccrs.PlateCarree(),
            s=1,
            lw=0,
            color="k",
        )

        # mark P5 position at start and end times
        ax.scatter(
            ds_gps.lon.sel(time=[t0, t1]),
            ds_gps.lat.sel(time=[t0, t1]),
            color="r",
            transform=ccrs.PlateCarree(),
        )

        # plot satellite tracks at the same time
        for sat in ds_sat.sat.values:
            ax.plot(
                ds_sat_flight.lon.sel(sat=sat),
                ds_sat_flight.lat.sel(sat=sat),
                transform=ccrs.PlateCarree(),
                label=sat,
                **sat_colors[sat],
            )

        ax.legend()

    # %%
    plt.close("all")
