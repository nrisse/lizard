"""
Tests the PAMTRA importer of ERA-5 and any sonde data. Here, we test with
radiosondes from Ny-Alesund
"""

import numpy as np

from lizard.readers.radiosonde import read_radiosonde
from lizard.pamtools.profile import PamProfile


class TestERA5PAM:
    def test_sonde(self):
        """
        Test with sonde data from Ny-Alesund
        """

        ds = read_radiosonde(time="2018-01-01 11:00:00")

        # set vertical coordinate to altitude
        ds = ds.swap_dims({"time": "alt"}).reset_coords()
        ds["time"] = ds["time"].mean()
        ds["lat"] = ds["lat"].mean()
        ds["lon"] = ds["lon"].mean()
        ds["wind10u"] = ds["wspeed"][0]
        ds["wind10v"] = 0
        ds["sfc_slf"] = 0
        ds["sfc_sif"] = 0
        ds["groundtemp"] = ds["temp"][0]

        # convert units
        ds["press"] = ds["press"] * 100
        ds["temp"] = ds["temp"] + 273.15
        ds["groundtemp"] = ds["groundtemp"] + 273.15

        grid_dimensions = {
            "grid_x": None,
            "grid_y": None,
            "grid_z": "alt",
        }

        varnames = {
            "lon": "lon",
            "lat": "lat",
            "timestamp": "time",
            "wind10u": "wind10u",
            "wind10v": "wind10v",
            "sfc_slf": "sfc_slf",
            "sfc_sif": "sfc_sif",
            "groundtemp": "groundtemp",
            "press": "press",
            "hgt": "alt",
            "relhum": "rh",
            "temp": "temp",
            "obs_height": None,
            "hydro_q": None,
            "sfc_type": None,
            "sfc_model": None,
            "sfc_refl": None,
        }
        
        pam_pro = PamProfile(
            ds,
            grid_dimensions,
            varnames,
            obs_height=np.array([0, 833000]),
            descriptor_file=None,
            remove_hydrometeors=False,
            kind="natural",
            ocean_model="TESSEM2",
            ocean_refl="L",
            land_model="TELSEM2",
            land_refl="L",
            sea_ice_model="TELSEM2",
            sea_ice_refl="L",
        )

        assert pam_pro.pam is not None
