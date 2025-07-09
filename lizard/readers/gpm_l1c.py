"""
Reader for GPM Common Calibrated Brightness Temperatures L1C V07 for a set
of instruments:
- SSMIS/F16
- SSMIS/F17
- SSMIS/F18
- MHS/Metop-A
- MHS/Metop-B
- MHS/Metop-C
- MHS/NOAA-18
- MHS/NOAA-19
- ATMS/SNPP
- ATMS/NOAA-20

Parts of this script are adapted from the GPROF_NN l1c.py module.

Final output format:
  - swaths are separated in an xarray.Dataset

Detailed information on the instrument swaths from the ATBD document:
MHS (p42, ATBD1.9):
  - S1: 89V, 157V, 183+/-1H, 183+/-3H, 190V
        1, 2, 3, 4, 5
(90 samples along the scan)

ATMS (p36, ATBD1.9):
  - S1: 23.8QV
        1
  - S2: 31.4QV
        2
  - S3: 88.2QV
        16
  - S4: 165QH, 183+/-7QH, 183+/-4.5QH, 183+/-3QH, 183+/-1.8QH, 183+/-1QH
        17, 18, 19, 20, 21, 22
(96 samples along the scan for every swath)

SSMIS (p26, ATBD1.9):
  - S1: 19V, 19H, 22V
        13, 12, 14
  - S2: 37V, 37H
        16, 15
  - S3: 150H, 183+/-1H, 183+/-3H, 183+/-7H
        8, 11, 10, 9
  - S4: 91V, 91H
        17, 18
(S1, S2: 90 samples along the scan. S3, S4: 180 samples along the scan)
(same number of scans)
(same scan repeat time)
(S1 and S2 are very close and S3 and S4 are very close)
(S1 and S2 pixels do not match positions of S3 and S4 pixels)

AMSR2 (p33, ATBD1.9):
  - S1: 10.65V 10.65H
        5, 6
  - S2: 18.7V 18.7H
        7, 8
  - S3: 23.8V 23.8H
        9, 10
  - S4: 36.5V 36.5H
        11, 12
  - S5: 89V 89H (A-Scan)
        13, 14
  - S6: 89V 89H (B-Scan)
        13, 14 (named 15, 16 when reading data, but is then merged)
(S1: 243 samples along scan)
(S2, S3, S4: positions differ slightly from S1)
(S5, S6: 486 samples along scan - twice as many as S1)
(coincidence: S1 pixels 1, 2, 3 = S5 pixels 1, 3, 5)
(scans of all swaths 10 km apart along track)
(S6 pixels are 15 km behind S1 and S5 pixels for same scan)
"""

import os
from glob import glob

import h5py
import numpy as np
import pandas as pd
import xarray as xr
from dotenv import load_dotenv
from pyproj import Transformer

load_dotenv()


FILENAME_SAT = {
    ("ATMS", "SNPP"): "NPP.ATMS",
    ("ATMS", "NOAA-21"): "NOAA21.ATMS",
    ("ATMS", "NOAA-20"): "NOAA20.ATMS",
    ("MHS", "NOAA-19"): "NOAA19.MHS",
    ("MHS", "NOAA-18"): "NOAA18.MHS",
    ("MHS", "Metop-C"): "METOPC.MHS",
    ("MHS", "Metop-B"): "METOPB.MHS",
    ("MHS", "Metop-A"): "METOPA.MHS",
    ("SSMIS", "DMSP-F18"): "F18.SSMIS",
    ("SSMIS", "DMSP-F17"): "F17.SSMIS",
    ("SSMIS", "DMSP-F16"): "F16.SSMIS",
    ("AMSR2", "GCOM-W"): "GCOMW1.AMSR2",
}

# channels within each instrument/swath in the specified order
SWATH_CHANNELS = {
    "MHS": {
        "S1": [1, 2, 3, 4, 5],
    },
    "ATMS": {
        "S1": [1],
        "S2": [2],
        "S3": [16],
        "S4": [17, 18, 19, 20, 21, 22],
    },
    "SSMIS": {
        "S1": [13, 12, 14],
        "S2": [16, 15],
        "S3": [8, 11, 10, 9],
        "S4": [17, 18],
    },
    "AMSR2": {
        "S1": [5, 6],
        "S2": [7, 8],
        "S3": [9, 10],
        "S4": [11, 12],
        "S5": [13, 14],
        "S6": [13, 14],
    },
}

# only W-/G-band channels sorted: frequency, v before h pol, 183 GHz in to out
CHANNELS_SORTED = {
    "ATMS": np.array([16, 17, 18, 19, 20, 21, 22]),
    "MHS": np.array([1, 2, 3, 4, 5]),
    "SSMIS": np.array([17, 18, 8, 9, 10, 11]),
    "AMSR2": np.array([13, 14]),
}

# only W-/G-band swaths with the first-mentioned containing W-band
SWATHS = {
    "MHS": np.array(["S1"]),
    "ATMS": np.array(["S3", "S4"]),
    "SSMIS": np.array(["S4", "S3"]),
    "AMSR2": np.array(["S5", "S6"]),
}


def read_gpm_l1c(
    instrument,
    satellite,
    granule,
    roi=None,
    center_lat=None,
    center_lon=None,
    max_distance=None,
    add_index=True,
):
    """
    Reads GPM L1C TB for a specific instrument/satellite/granule in a given
    region of interest.
    Only W- and G-band channels are imported with footprint coordinates of the
    W-band used also at G-band (for SSMIS and ATMS). Slight differences
    between these coordinates might occur for SSMIS.
    Generally, W- and G-band share almost the same footprint location.

    For AMSR2, the scans A and B are merged into a single swath.

    Example:
    ds = read_gpm_l1c(
        instrument='ATMS',
        satellite='NOAA-20',
        granule='007068',
        roi=[-10, 20, 78, 83],
    )

    Possible improvements:
    - treat swaths independent. currently I need to specify one swath as
      geographic position, which must not be the same for the tb data!

    Documentation:
    https://arthurhou.pps.eosdis.nasa.gov/Documents/L1C_ATBD_v1.9_GPMV07.pdf

    Parameters
    ----------
    instrument: instrument name.
    satellite: spacecraft name.
    granule: granule number to be read
    roi: only scans that are at least partly rectangular roi are kept.
    center_lat: central latitude (alternative to roi)
    center_lon: central longitude (alternative to roi)
    max_distance: maximum distance from central latitude/longitude point
      (alternative to roi)
    add_index: adds index for unique footprints within granule

    Returns
    -------
    xr.Dataset with calibrated brightness temperatures
    """

    kwds = dict(
        instrument=instrument,
        satellite=satellite,
        granule=granule,
        roi=roi,
        center_lat=center_lat,
        center_lon=center_lon,
        max_distance=max_distance,
        add_index=add_index,
    )

    ds = None
    if instrument == "MHS":
        ds = read_gpm_l1c_swath(swath=SWATHS[instrument][0], **kwds)

    elif instrument in ["ATMS", "SSMIS"]:
        ds1 = read_gpm_l1c_swath(
            sg=SWATHS[instrument][0], st=SWATHS[instrument][0], **kwds
        )

        # merge tbs from second swath
        ds2 = read_gpm_l1c_swath(
            sg=SWATHS[instrument][0], st=SWATHS[instrument][1], **kwds
        )
        ds = ds1.combine_first(ds2)

    elif instrument == "AMSR2":
        ds1 = read_gpm_l1c_swath(swath=SWATHS[instrument][0], **kwds)
        ds2 = read_gpm_l1c_swath(swath=SWATHS[instrument][1], **kwds)

        # merge multiplying B-scans with -1
        ds2["x"] = -ds2["x"]
        ds2["footprint_id"] = -ds2["footprint_id"]

        # concatenate along track
        ds = xr.concat([ds1, ds2], dim="x")

    # sort channels
    ds = ds.sel(channel=CHANNELS_SORTED[instrument])

    return ds


def read_gpm_l1c_swaths(
    instrument,
    satellite,
    granule,
    roi=None,
    center_lat=None,
    center_lon=None,
    max_distance=None,
    add_index=True,
):
    """
    Reads GPS L1C calibrated brightness temperature for a specific instrument.
    Returns a dict of xarray datasets for every swath of the instrument.

    Example:
    swath_dct = read_gpm_l1c_swaths(
        instrument='ATMS',
        satellite='NOAA-20',
        granule='007068',
        roi=[-10, 20, 78, 83],
    )

    Documentation:
    https://arthurhou.pps.eosdis.nasa.gov/Documents/L1C_ATBD_v1.9_GPMV07.pdf

    Parameters
    ----------
    instrument: instrument name.
    satellite: spacecraft name.
    granule: granule number to be read
    roi: only scans that are at least partly rectangular roi are kept.
    center_lat: central latitude (alternative to roi)
    center_lon: central longitude (alternative to roi)
    max_distance: maximum distance from central latitude/longitude point
      (alternative to roi)
    add_index: adds index for unique footprints within granule

    Returns
    -------
    dictionary with xarray datasets containing calibrated brightness
    temperatures for each swath.
    """

    swath_dct = {}
    for swath in list(SWATH_CHANNELS[instrument]):
        swath_dct[swath] = read_gpm_l1c_swath(
            instrument=instrument,
            satellite=satellite,
            granule=granule,
            roi=roi,
            center_lat=center_lat,
            center_lon=center_lon,
            max_distance=max_distance,
            swath=swath,
            add_index=add_index,
        )

    return swath_dct


def read_gpm_l1c_swath(
    instrument,
    satellite,
    granule,
    roi=None,
    center_lat=None,
    center_lon=None,
    max_distance=None,
    swath=None,
    add_index=True,
    sg=None,
    st=None,
):
    """
    Reads specific swath of GPS L1C TB. There is an option to read the tb of
    one swath and the geographic position of another swath. This is done
    for G- and W-band channels which are on almost the same geographic
    location.

    Example:
    ds = read_gpm_l1c_swath(
        instrument='ATMS',
        satellite='NOAA-20',
        granule='007068',
        roi=[-10, 20, 78, 83],
        swath='S4',
    )

    Documentation:
    https://arthurhou.pps.eosdis.nasa.gov/Documents/L1C_ATBD_v1.9_GPMV07.pdf

    Parameters
    ----------
    instrument: instrument name.
    satellite: spacecraft name.
    granule: granule number to be read
    roi: only scans that are at least partly rectangular roi are kept.
    center_lat: central latitude (alternative to roi)
    center_lon: central longitude (alternative to roi)
    max_distance: maximum distance from central latitude/longitude point
      (alternative to roi)
    swath: instrument swath (e.g. S1)
    add_index: adds index for unique footprints within granule
    sg: swath for geographic location
    st: swath for tb

    Returns
    -------
    dictionary with xarray datasets containing calibrated brightness
    temperatures for each swath.
    """

    if sg is None and st is None:
        sg = swath
        st = swath

    granule = str(granule).zfill(6)  # allows for integer granule numbers
    file = glob(
        os.path.join(
            os.environ["PATH_SAT"],
            "gpm_l1c",
            f"1C.{FILENAME_SAT[(instrument, satellite)]}.XCAL*.{granule}.V07*.HDF5",
        )
    )[0]

    with h5py.File(file, "r") as f:
        # to store as xarray dataset
        data = dict()

        dims_swath = f[sg]["Latitude"][:].shape

        # reduce to region of interest
        if isinstance(roi, list):
            ix = roi_index(
                lat=f[sg]["Latitude"][:], lon=f[sg]["Longitude"][:], roi=roi
            )
        else:
            ix = distance_index(
                lat=f[sg]["Latitude"][:],
                lon=f[sg]["Longitude"][:],
                center_lat=center_lat,
                center_lon=center_lon,
                max_distance=max_distance,
            )

        # get scan time
        time = extract_time(swath_data=f[sg])
        data["scan_time"] = ("x", time[ix])
        data["sc_orientation"] = ("x", f[sg]["SCstatus"]["SCorientation"][ix])
        data["sc_lat"] = ("x", f[sg]["SCstatus"]["SClatitude"][ix])
        data["sc_lon"] = ("x", f[sg]["SCstatus"]["SClongitude"][ix])
        data["sc_alt"] = ("x", f[sg]["SCstatus"]["SCaltitude"][ix])
        data["lat"] = (("x", "y"), f[sg]["Latitude"][ix])
        data["lon"] = (("x", "y"), f[sg]["Longitude"][ix])
        data["incidence_angle"] = (
            ("x", "y"),
            f[sg]["incidenceAngle"][ix, :, 0],
        )
        data["quality"] = (("x", "y"), f[sg]["Quality"][ix])
        data["tb"] = (("x", "y", "channel"), f[st]["Tc"][ix, :, :])

        ds = xr.Dataset(data)

        # add coordinates
        x_ix = np.arange(0, dims_swath[0], dtype="int")[ix]
        y_ix = np.arange(0, dims_swath[1], dtype="int")
        ds.coords["x"] = x_ix
        ds.coords["y"] = y_ix
        ds.coords["channel"] = SWATH_CHANNELS[instrument][st]

        # add unique footprint index
        if add_index:
            ds = ds.stack({"xy": ("x", "y")})
            ds["footprint_id"] = (
                "xy",
                np.ravel_multi_index((ds.x.values, ds.y.values), dims_swath),
            )
            ds = ds.unstack()
            ds["footprint_id"].attrs = dict(
                standard_name="footprint_id",
                long_name="footprint id",
                description="unique footprint id within granule defined by "
                "counting first the across-track (y) values for "
                "each "
                "along-track (x) bin",
            )

        # add global attributes
        ds.attrs = {
            ab.split("=")[0]: ab.split("=")[1]
            for ab in f.attrs["FileHeader"].decode().split(";\n")[:-1]
        }

    return ds


def extract_time(swath_data):
    """
    This function extracts the time from a swath and converts it into a numpy
    array.

    Parameters
    ----------
    swath_data: data of a swath (e.g. f['S1'])

    Returns
    -------
    time: scan time numpy array
    """

    time = {
        "year": swath_data["ScanTime"]["Year"],
        "month": swath_data["ScanTime"]["Month"],
        "day": swath_data["ScanTime"]["DayOfMonth"],
        "hour": swath_data["ScanTime"]["Hour"],
        "minute": swath_data["ScanTime"]["Minute"],
        "second": swath_data["ScanTime"]["Second"],
        "millisecond": swath_data["ScanTime"]["MilliSecond"],
    }

    time = pd.to_datetime(time).values

    return time


def roi_index(lat, lon, roi):
    """
    Returns along-track index where at least one pixel of the scan lies within
    the region of interest.

    Parameters
    ----------
    lat: latitude of satellite footprints
    lon: longitude of satellite footprints
    roi: region of interest as list containing [lon0, lon1, lat0, lat1]

    Returns
    -------
    ix: index of length number of scans
    """

    lon0, lon1, lat0, lat1 = roi

    ix = np.any(
        (lon >= lon0) * (lon < lon1) * (lat >= lat0) * (lat < lat1), axis=1
    )

    return ix


def distance_index(lat, lon, center_lat, center_lon, max_distance):
    """
    Returns along-track index where at least one pixel of the scan lies within
    a certain distance from a center point. This function is an alternative
    to roi_index() for the Arctic.

    Parameters
    ----------
    lat: latitude
    lon: longitude
    center_lat: central latitude
    center_lon: central longitude
    max_distance: maximum distance from central location in meters

    Returns
    -------
    ix: index of length number of scans
    """

    # project coordinates into polar stereographic projection
    sat_points = np.array(project_crs(lon=lon, lat=lat)).T
    center_point = np.array(project_crs(lon=center_lon, lat=center_lat))

    distance = np.linalg.norm(sat_points - center_point, axis=2)

    ix = np.any(distance <= max_distance, axis=0)

    return ix


def time_index(scan_time, time, time_offset):
    """
    Applies temporal filtering on the data by comparing the mean scan time
    with an input time and a maximum time offset in hours.

    Parameters
    ----------
    scan_time: scan time of satellite
    time: central time for temporal filter
    time_offset: time offset around the central time for temporal filter. Data
      type: np.timedelta64

    Returns
    -------
    ix: index of length number of scans
    """

    ix = np.abs(scan_time - time) <= time_offset

    return ix


def get_files(instrument, satellite, date=None, time=None, time_offset=None):
    """
    This function allows to read only specific satellite files based on a
    temporal filter. The most basic application is to read files based on the
    start date of the orbit. A more advanced application is a time window
    around midnight, e.g. 23 UTC, where radiosondes are lauched. If this is
    specified, the function reads only orbits that start before
    and end after this time window plus two hours.

    Please specify only either the date or the time and time_offset variables.

    Parameters
    ----------
    instrument: satellite instrument
    satellite: satellite
    date: date of interest
    time: central time for temporal filter
    time_offset: time offset around the central time for temporal filter. Data
      type: np.timedelta64

    Returns
    -------
    file: all files that either start on
    """

    # check input
    if date is None:
        assert time is not None and time_offset is not None

    if time is None and time_offset is None:
        assert date is not None

    if time is None and time_offset is None:
        date = pd.Timestamp(date).strftime("%Y%m%d")
        files = sorted(
            glob(
                os.path.join(
                    os.environ["PATH_SAT"],
                    "gpm_l1c",
                    f"1C.{FILENAME_SAT[(instrument, satellite)]}.XCAL*-V.{date}-S*.HDF5",
                )
            )
        )

    else:
        files = np.sort(
            glob(
                os.path.join(
                    os.environ["PATH_SAT"],
                    "gpm_l1c",
                    f"1C.{FILENAME_SAT[(instrument, satellite)]}.XCAL*-V.*-S*.HDF5",
                )
            )
        )

        # get start time from start date and start time
        start_time = [s[-41:-33] + s[-31:-25] for s in files]
        start_time = pd.to_datetime(start_time, format="%Y%m%d%H%M%S").values

        # get end time from start date and end time
        end_time = [s[-41:-33] + s[-23:-17] for s in files]
        end_time = pd.to_datetime(end_time, format="%Y%m%d%H%M%S").values

        # correction of end time by one day if needed
        next_day = (end_time - start_time) < np.timedelta64(0, "s")
        end_time[next_day] += np.timedelta64(1, "D")

        ix = (np.abs(start_time - time) <= time_offset) | (
            np.abs(end_time - time) < time_offset
        )
        files = list(files[ix])

    return files


def in_roi(
    instrument,
    satellite,
    date=None,
    roi=None,
    center_lat=None,
    center_lon=None,
    max_distance=None,
    time=None,
    time_offset=None,
):
    """
    Returns granules that lies at least partly within a given region of
    interest. The temporal filter can be either a date (start date of orbit
    over Antarctica) or a time and a time offset. The satellilte scan time is
    used as a reference for each scan when a time and a time offset is chosen.
    This also works around midnight and automatically finds data of the
    previous or next day, if they fall within the time window.

    Example:
    roi_check = in_roi(
        instrument='ATMS',
        satellite='NOAA-20',
        date=np.datetime64('2019-03-31'),
        roi=[-10, 20, 78, 83],
    )

    Parameters
    ----------
    instrument: satellite instrument
    satellite: satellite
    date: date of interest
    roi: region of interest
    center_lat: central latitude (alternative to roi)
    center_lon: central longitude (alternative to roi)
    max_distance: maximum distance from central location in meters (alternative
      to roi)
    time: central time for temporal filter
    time_offset: time offset around the central time for temporal filter. Data
      type: np.timedelta64

    Returns
    -------
    granules: list of granules within roi
    """

    # get all files on date
    files = get_files(
        instrument=instrument,
        satellite=satellite,
        date=date,
        time=time,
        time_offset=time_offset,
    )

    granules = []
    for file in files:
        with h5py.File(file, "r") as f:
            s0 = SWATHS[instrument][0]

            if isinstance(roi, list):
                ix = roi_index(
                    lat=f[s0]["Latitude"][:],
                    lon=f[s0]["Longitude"][:],
                    roi=roi,
                )
            else:
                ix = distance_index(
                    lat=f[s0]["Latitude"][:],
                    lon=f[s0]["Longitude"][:],
                    center_lat=center_lat,
                    center_lon=center_lon,
                    max_distance=max_distance,
                )

            if time is not None:
                ix_t = time_index(
                    scan_time=extract_time(f[s0]),
                    time=time,
                    time_offset=time_offset,
                )

                # merge temporal and spatial filters
                ix = ix * ix_t

        if np.any(ix):
            granules.append(file.split(".")[-3])

    return granules


def project_crs(lon, lat):
    """
    Parameters
    ----------
    lon: longitude in degrees
    lat: latitude in degrees

    Returns
    -------
    x: x-coordinate of north polar stereographic projection
    y: y-coordinate of north polar stereographic projection
    """

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3413")
    x, y = transformer.transform(lat, lon)

    return x, y


def get_granules(
    ins_sat,
    date,
    roi=None,
    center_lat=None,
    center_lon=None,
    max_distance=None,
    time=None,
    time_offset=None,
):
    """
    Get granules of a given instrument at a certain date within roi or within
    certain distance from a center point. Additionally, a specific time and a
    time offset can be specified.

    Parameters
    ----------
    ins_sat: list of instrument and satellite tupels (e.g.: [('SNPP', 'ATMS')])
    roi: region of interest
    date: date of interest
    center_lat: central latitude (alternative to roi)
    center_lon: central longitude (alternative to roi)
    max_distance: maximum distance from central location in meters (alternative
      to roi)
    time: central time for temporal filter
    time_offset: time offset around the central time for temporal filter. Data
      type: np.timedelta64

    Returns
    -------
    granules_dct: dictionary of granules
    """

    granules_dct = dict()
    for satellite, instrument in ins_sat:
        granules_dct[f"{satellite}_{instrument}"] = in_roi(
            instrument,
            satellite,
            date,
            roi=roi,
            center_lat=center_lat,
            center_lon=center_lon,
            max_distance=max_distance,
            time=time,
            time_offset=time_offset,
        )

    return granules_dct


def flag_gpml1c(ds, verbose=False):
    """
    Flags gpm l1c based on the provided quality mask and an additional filter
    for corrupt scans. A very strict filter is applied that only uses
    those pixels of "good" quality (quality flag = 0). The filter for corrupt
    scans sets those scans to nan where the across-track standard deviation is
    smaller than 0.1 K. Such low values are unrealistic.

    See documentation for quality flag meanings:
    https://arthurhou.pps.eosdis.nasa.gov/Documents/L1C_ATBD_v1.9_GPMV07.pdf#
    Sensor-specific quality flags:
        p29 (SSMIS), p35 (AMSR2), p38 (ATMS), p44 (MHS)
    Errors (negative flag): tb is set to missing values (-9999)
    Warnings (positive flag): tb is retained

    Parameters
    ----------
    ds: xarray dataset of a granule
    verbose: if True, prints old and new value ranges

    Returns
    -------
    ds: same dataset with flagged Tb set to nan
    """

    # set unrealistic longitude and latitude to nan
    ds["lat"] = ds.lat.where(ds["lat"] > -900)
    ds["lon"] = ds.lon.where(ds["lon"] > -900)

    # set missing tb to nan (this included all errors)
    ds["tb"] = ds.tb.where(ds["tb"] > 0)

    # filter calculation: True=remove values
    fltr = ds.tb.std("y") < 0.1

    # number of pixels/scans that are filtered
    n = np.sum(fltr.values)

    # data range before filter
    tb00 = ds["tb"].min().item()
    tb11 = ds["tb"].max().item()

    # apply filters
    ds["tb"] = ds.tb.where(~fltr)

    if verbose:
        print(f"Value range of instrument: {tb00}..{tb11}")
        if n > 0:
            tb0 = ds["tb"].min().item()
            tb1 = ds["tb"].max().item()
            print(f"New value range of instrument: {tb0}..{tb1}")

            flags = np.unique(ds.quality.where(fltr).values)
            flags = flags[~np.isnan(flags)]
            print(f"{n} scans removed by own scan line filter: {flags}")

    return ds
