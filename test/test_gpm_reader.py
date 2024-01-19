"""
Test GPM reader
"""

import os

import numpy as np

from lizard.readers.gpm_l1c import get_granules, read_gpm_l1c

os.environ["PATH_SAT"] = os.path.join(os.environ["PATH_SEC"], "data/sat")


class TestGPMReader:
    def test_read_gpm_l1c_roi(self):
        instrument = "ATMS"
        satellite = "SNPP"
        granule = "038575"
        roi = [-180, 180, -90, 90]
        ds = read_gpm_l1c(
            instrument, satellite, granule, roi=roi, add_index=True
        )

        assert dict(ds.dims) == {"x": 2258, "y": 96, "channel": 7}

    def test_read_gpm_l1c_distance(self):
        instrument = "ATMS"
        satellite = "SNPP"
        granule = "041324"
        center_lon = 45
        center_lat = 85
        max_distance = 200000
        ds = read_gpm_l1c(
            instrument,
            satellite,
            granule,
            center_lon=center_lon,
            center_lat=center_lat,
            max_distance=max_distance,
            add_index=True,
        )

        assert dict(ds.dims) == {"x": 24, "y": 96, "channel": 7}

    def test_get_granules(self):
        ins_sat = [("NOAA-18", "MHS")]
        center_lon = 0
        center_lat = 82
        max_distance = 200000
        time = np.datetime64("2015-06-10 11:00:00")
        time_offset = np.timedelta64(50, "m")
        granules = get_granules(
            ins_sat,
            date=None,
            roi=None,
            center_lat=center_lat,
            center_lon=center_lon,
            max_distance=max_distance,
            time=time,
            time_offset=time_offset,
        )

        assert list(granules.values()) == [["051812"]]
