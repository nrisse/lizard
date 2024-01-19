"""
Creates PAMTRA profile from any source. Current implementations:
- any profile from point measurement, 1D, or 2D (all transformations need to
be specified by the user)
- ERA-5 specifically (performs all required transformations)
"""

import datetime

import numpy as np
import pyPamtra
import xarray as xr

from lizard.pamtools.pamtra_tools import PamtraSurface
from lizard.readers.era5 import (
    read_era5_pressure_levels,
    read_era5_single_levels,
)

PAM_VARS = [
    "lon",
    "lat",
    "timestamp",
    "wind10u",
    "wind10v",
    "sfc_slf",
    "sfc_sif",
    "groundtemp",
    "press",
    "hgt",
    "relhum",
    "temp",
    "obs_height",
    "hydro_q",
    "sfc_type",
    "sfc_model",
    "sfc_refl",
]


class PamProfile:
    """
    Converts ERA-5 NetCDF single- and pressure-levels to PAMTRA object.
    """

    def __init__(
        self,
        ds,
        grid_dimensions,
        varnames,
        obs_height=None,
        descriptor_file=None,
        remove_hydrometeors=True,
        kind="natural",
        ocean_model="TESSEM2",
        ocean_refl="L",
        land_model="TELSEM2",
        land_refl="L",
        sea_ice_model="TELSEM2",
        sea_ice_refl="L",
    ):
        """
        Read ERA-5 for a given time step and spatial extent to PAMTRA. The
        surface properties are set either natural depending on
        sea ice and land fraction or idealized as fixed emissivity value.

        Units
        -----
        Pressure: Pascal
        Height: meter
        Temperature: Kelvin
        Wind: m/s
        Relative humidity: %

        Notes
        -----
        Relative humidities above 100 % or below 0 % are set to 100 % and 0 %,
        respectively.

        Parameters
        -------
        ds: xarray.Dataset
            Dataset containing the data to be transformed
        grid_dimensions: dict
            Dictionary containing the dimensions of the grid. The keys are the
            names of the dimensions in the PAMTRA profile, the values are the
            names of the dimensions in the dataset. Example: grid_x in PAMTRA
            is longitude in the dataset.
        varnames: dict
            Dictionary containing the names of the variables in the PAMTRA
            profile and the names of the variables in the dataset.
        obs_height: np.array
            Observation height(s) in meter.
        descriptor_file: str
            Path to the descriptor file.
        remove_hydrometeors: bool
            If True, all hydrometeor variables are set to zero.
        kind: defines they way, surface types are identified. Either natural or
            idealized are possible. For idealized, a fixed emissivity is used
            for all surfaces. For natural, the emissivity is taken from one of
            the emissivity models.
        ocean_model: surface model for ocean
        land_model: surface model for land
        sea_ice_model: surface model for sea ice
        ocean_refl: reflection type over ocean
        land_refl: reflection type over land
        sea_ice_refl: reflection type over sea ice
        """

        self.ds = ds
        self.obs_height = obs_height
        self.grid_dimensions = grid_dimensions
        self.varnames = varnames
        self.descriptor_file = descriptor_file
        self.remove_hydrometeors = remove_hydrometeors
        self.kind = kind
        self.ocean_model = ocean_model
        self.ocean_refl = ocean_refl
        self.land_model = land_model
        self.land_refl = land_refl
        self.sea_ice_model = sea_ice_model
        self.sea_ice_refl = sea_ice_refl

        self.pam = pyPamtra.pyPamtra()

        if descriptor_file is not None:
            self.pam.df.readFile(self.descriptor_file)

        # transform dataset to the shape required by PAMTRA
        self.transform_ds()

        # write to pypamtra object
        self.to_pamtra()

    @classmethod
    def from_era5(cls, time, extent, **kwargs):
        """
        Reads ERA-5 single and pressure levels data

        This example runs for ERA-5:
        grid_dimensions = {
            "grid_x": "longitude",
            "grid_y": "latitude",
            "grid_z": "level",
        }

        varnames = {
            "lon": "longitude",
            "lat": "latitude",
            "timestamp": "time",
            "wind10u": "u10",
            "wind10v": "v10",
            "sfc_slf": "lsm",
            "sfc_sif": "siconc",
            "groundtemp": "skt",
            "press": "level",
            "hgt": "hgt",
            "relhum": "r",
            "temp": "t",
            "obs_height": None,
            "hydro_q": None,
            "sfc_type": None,
            "sfc_model": None,
            "sfc_refl": None,
        }

        PamProfile.from_era5(
            time=np.datetime64('2017-05-23 00:12'),
            extent=[-10, 10, 80, 82],
            grid_dimensions=grid_dimensions,
            varnames=varnames
        )

        Parameters
        ----------
        time: time step at which ERA-5 data is read (specify hour)
        extent: specify extent of final pamtra profile [lon0, lon1, lat0, lat1]
            lon = [-180, 180], lat = [-90, 90]
        kwargs: keyword arguments passed to PamProfile
        """

        if type(time) == np.datetime64:
            time = time.astype(datetime.datetime)
        else:
            time = time

        ds_sl = read_era5_single_levels(time)
        ds_pl = read_era5_pressure_levels(time)

        # rename surface height
        ds_sl = ds_sl.rename({"z": "z_sfc"})

        ds = xr.merge([ds_sl, ds_pl])

        # get time step
        ds = ds.sel(time=time, method="nearest").reset_coords()

        # get subset region
        if extent is not None:
            lon0, lon1, lat0, lat1 = extent
            ds = ds.sel(
                longitude=slice(lon0, lon1), latitude=slice(lat1, lat0)
            )

        # reverse pressure grid
        ds = ds.sel(level=ds.level[::-1])

        # reverse latitude grid
        ds = ds.sel(latitude=ds.latitude[::-1])

        # pressure to pascal
        ds["level"] *= 100  # to Pa

        # geopotential to height
        g = 9.80665  # Earth's gravitational acceleration
        ds["hgt"] = ds["z"] / g

        # set negative heights to -200 m
        ds["hgt"] = ds["hgt"].where(ds["hgt"] > -200, -200)

        # combine hydrometeor variables
        vars_hyd = ["clwc", "ciwc", "crwc", "cswc"]
        ds.coords["hyd"] = vars_hyd
        ds["hydro_q"] = xr.concat([ds[h] for h in vars_hyd], dim="hyd")
        ds["hydro_q"] = ds["hydro_q"].where(ds["hydro_q"] > 0, 0)
        ds = ds.drop_vars(ds.hyd.values)  # drop individual variables

        return cls(ds, **kwargs)

    def filter_relhum(self, rh_var):
        """
        Prepares relative humidity
        """

        self.ds[rh_var] = self.ds[rh_var].where(
            self.ds[rh_var] < 100, 100
        )  # limit to 100 %
        self.ds[rh_var] = self.ds[rh_var].where(
            self.ds[rh_var] > 0, 0
        )  # limit to 0 %

    def convert_time(self):
        """
        Prepares time
        """

        # time to unix time
        self.ds["time"] = (
            self.ds["time"].dims,
            (self.ds.time.values - np.datetime64("1970-01-01"))
            .astype("timedelta64[s]")
            .astype("int"),
        )

    def expand_variables(self):
        """
        Expands variables to the grid dimensions (grid_x, grid_y) if they are
        not yet a function of grid_x and grid_y.

        This function only takes care of surface variables.
        """

        var_lst = PAM_VARS.copy()
        var_lst.remove("sfc_type")
        var_lst.remove("sfc_model")
        var_lst.remove("sfc_refl")
        if "hydro_q" not in self.ds:
            var_lst.remove("hydro_q")

        # expand variables until they are a function of grid_x and grid_x
        for v in var_lst:
            # grid_y is missing
            if "grid_x" in self.ds[v].dims and "grid_y" not in self.ds[v].dims:
                self.ds[v] = self.ds[v].expand_dims({"grid_y": self.ds.grid_y})

            # grid_x is missing
            elif (
                "grid_x" not in self.ds[v].dims and "grid_y" in self.ds[v].dims
            ):
                self.ds[v] = self.ds[v].expand_dims({"grid_x": self.ds.grid_x})

            # both dimensions are missing
            elif (
                "grid_x" not in self.ds[v].dims
                and "grid_y" not in self.ds[v].dims
            ):
                self.ds[v] = self.ds[v].expand_dims(
                    {"grid_x": self.ds.grid_x, "grid_y": self.ds.grid_y}
                )

    def add_obs_height(self):
        """
        Prepare observation height if it is not given yet. This function will
        assume that the same observation height(s) are used for all grid
        points. If this is not the case, the user needs to specify the
        observation height for each grid point manually.

        Parameters
        ----------
        obs_height : np.array
            Observation height(s) in meter.
        """

        if self.obs_height is not None:
            self.ds.coords["outlevel"] = np.arange(len(self.obs_height))
            self.ds["obs_height"] = ("outlevel", self.obs_height)

            # make 3d variable by expanding it to the grid dimensions
            self.ds["obs_height"] = self.ds["obs_height"].expand_dims(
                {"grid_x": self.ds.grid_x, "grid_y": self.ds.grid_y}
            )

    def rename(self, varnames):
        """
        Renames variables to the name expected by PAMTRA
        """

        self.ds = self.ds.rename(
            {v: k for k, v in varnames.items() if v is not None}
        )

    def prepare_surface(self):
        """
        Prepares surface using PamtraSurface module
        """

        pam_pro = PamtraSurface(
            ds=self.ds,
            kind=self.kind,
            ocean_model=self.ocean_model,
            ocean_refl=self.ocean_refl,
            land_model=self.land_model,
            land_refl=self.land_refl,
            sea_ice_model=self.sea_ice_model,
            sea_ice_refl=self.sea_ice_refl,
        )
        self.ds = pam_pro.ds

    def set_hydrometeors_to_zero(self):
        """
        Sets all hydrometeor variables to zero.
        """

        self.ds["hydro_q"] = xr.zeros_like(self.ds["hydro_q"])

    def transform_ds(self):
        """
        Converts dataset to PAMTRA profile.
        """

        for pam_dim, dim in self.grid_dimensions.items():
            if dim is not None:
                # create dimension first as variable and then swap with current
                # dimension
                self.ds[pam_dim] = (
                    dim,
                    np.arange(0, len(self.ds[dim])),
                )
                self.ds = self.ds.swap_dims({dim: pam_dim}).reset_coords()

            else:
                # create dimension of length 1
                self.ds.coords[pam_dim] = (pam_dim, np.array([0]))

        # applies valid range to relative humidity values
        self.filter_relhum(rh_var=self.varnames["relhum"])

        # converts time variable to unix time
        self.convert_time()

        # prepares observation height variable
        self.add_obs_height()

        # rename variables
        self.rename(self.varnames)

        # expand dimensions
        self.expand_variables()

        # make sure, that order of dimensions is correct
        if "hyd" in self.ds.dims:
            self.ds = self.ds.transpose(
                "grid_x", "grid_y", "grid_z", "outlevel", "hyd"
            )

        else:
            self.ds = self.ds.transpose(
                "grid_x", "grid_y", "grid_z", "outlevel"
            )

        # add surface model
        # TODO: change it so that it only creates surface if it is not given
        self.prepare_surface()

        # remove hydrometeors if needed
        if self.remove_hydrometeors:
            self.set_hydrometeors_to_zero()

    def to_pamtra(self):
        """
        Creates pamtra profile.
        """

        pam_vars = PAM_VARS.copy()

        # without hydrometeors
        if "hydro_q" not in self.ds:
            pam_vars.remove("hydro_q")

            # add an empty hydrometeor
            # TODO: make it flexible and add any hydrometeors by user
            self.pam.df.addHydrometeor(
                (
                    "ice",
                    -99.0,
                    -1,
                    917.0,
                    130.0,
                    3.0,
                    0.684,
                    2.0,
                    3,
                    1,
                    "mono_cosmo_ice",
                    -99.0,
                    -99.0,
                    -99.0,
                    -99.0,
                    -99.0,
                    -99.0,
                    "mie-sphere",
                    "heymsfield10_particles",
                    0.0,
                )
            )

        pam_profile = dict()
        for var in pam_vars:
            pam_profile[var] = self.ds[var].values
        self.pam.createProfile(**pam_profile)
