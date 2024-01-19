"""
Collection of functions usefult when working with PAMTRA

TODO: add atmospheric layers as well in their grid as they are used in pamtra
and as they are availabel. not sure what temp and temp_lev differences are!

add_obs_height_to_layer --> what happens here exactly?

hydro_n
hydro_q
hydro_reff

add names of hydrometeors if possible - they must be in descriptor file or?
maybe also add content of descriptor file to keep track?
"""


import datetime

import numpy as np
import pandas as pd
import xarray as xr


def pam_to_xarray(pam, split_angle=True):
    """
    Converts a selection of pyPamtra variables to an xarray.Dataset with
    meta information. So far, this function is only created for passive
    simulations. Allows for fast analysis of the pamtra simulation
    and quick examples without having to remember index positions

    Based on the writeResultsToNetCDF of pyPamtra core.py script. Some
    variables were renamed and obs_height is added (was outlevels before)
    to make the new naming consistent with the one in the different pam
    dictionaries.

    The function could be added to the core.py script, one it is extended
    by active variables and is getting more flexible on what is written to
    xarray, which could be solved by a yaml configuration file.

    Input
    pam: pyPamtra object
        pamtra object after simulation of the brightness temperatures and
        calculation of integrated values.
    split_angle: bool
        weather to split the angle which is defined from 0-180 with 0 as
        downwelling zenith and 180 as upwelling nadir into two additional
        dimensions 'direction' which is either up or down referring to the
        direction of radiation flux not to the instrument view and
        'incidence_angle' which is 0 in the vertical (zenith or nadir)
        and 90 along the horizon. This simplifies the estimation of the
        specular reflection right above the surface, where incidence
        and reflection angle are equal.

    Returns
    -------
    ds_pam: xarray.Dataset containing a selection of pamtra variables
    """

    ds_pam = xr.Dataset()

    # coordinates
    ds_pam.coords["grid_x"] = np.arange(0, pam.p["ngridx"], dtype="int")
    ds_pam.coords["grid_y"] = np.arange(0, pam.p["ngridy"], dtype="int")
    ds_pam.coords["frequency"] = np.array(pam.set["freqs"], dtype="float")
    ds_pam.coords["angle"] = np.array(pam.r["angles_deg"], dtype="float")
    ds_pam.coords["outlevel"] = np.arange(0, pam.p["noutlevels"], dtype="int")
    ds_pam.coords["polarization"] = np.array(["V", "H"])
    ds_pam.coords["hydro_class"] = np.arange(pam.p["hydro_wp"].shape[2])
    # ds_pam.coords['lev'] = np.arange(pam.p['max_nlyrs']+1)

    # coordinate attributes
    ds_pam["grid_x"].attrs = dict(long_name="pamtra grid x-axis")
    ds_pam["grid_y"].attrs = dict(long_name="pamtra grid y-axis")
    ds_pam["frequency"].attrs = dict(long_name="frequency", units="GHz")
    ds_pam["angle"].attrs = dict(long_name="viewing angle", units="deg")
    ds_pam["outlevel"].attrs = dict(long_name="outlevel")
    ds_pam["polarization"].attrs = dict()
    ds_pam["hydro_class"].attrs = dict(long_name="hydrometeor class")

    # variables
    dim_2d = ("grid_x", "grid_y")
    dim_3d = ("grid_x", "grid_y", "outlevel")
    # dim_3d_lev = ('grid_x', 'grid_y', 'lev')
    dim_3d_hydro = ("grid_x", "grid_y", "hydro_class")
    dim_5d = ("grid_x", "grid_y", "polarization", "frequency", "angle")
    dim_6d = (
        "grid_x",
        "grid_y",
        "outlevel",
        "angle",
        "frequency",
        "polarization",
    )

    # 2d variables
    ds_pam["model_i"] = (dim_2d, pam.p["model_i"])
    ds_pam["model_i"].attrs = dict(long_name="model grid i-direction")

    ds_pam["model_j"] = (dim_2d, pam.p["model_j"])
    ds_pam["model_j"].attrs = dict(long_name="model grid j-direction")

    ds_pam["nlyrs"] = (dim_2d, pam.p["nlyrs"])
    ds_pam["nlyrs"].attrs = dict(long_name="number of vertical layers")

    ds_pam["time"] = (
        dim_2d,
        np.datetime64("1970-01-01")
        + pam.p["unixtime"].astype("timedelta64[s]"),
    )
    ds_pam["time"].attrs = dict(long_name="time")
    ds_pam["time"].encoding = dict(units="seconds since 1970-01-01 00:00:00")

    ds_pam["lon"] = (dim_2d, pam.p["lon"])
    ds_pam["lon"].attrs = dict(long_name="longitude", units="deg")

    ds_pam["lat"] = (dim_2d, pam.p["lat"])
    ds_pam["lat"].attrs = dict(long_name="latitude", units="deg")

    ds_pam["sfc_type"] = (dim_2d, pam.p["sfc_type"])
    ds_pam["sfc_type"].attrs = dict(
        long_name="surface type",
        flag_values=np.array([0, 1]),
        flag_meanings=np.array(["water", "land"], dtype="str"),
    )

    ds_pam["groundtemp"] = (dim_2d, pam.p["groundtemp"])
    ds_pam["groundtemp"].attrs = dict(
        long_name="ground temperature", units="K"
    )

    ds_pam["sfc_salinity"] = (dim_2d, pam.p["sfc_salinity"])
    ds_pam["sfc_salinity"].attrs = dict(
        long_name="sea surface salinity", units="psu"
    )

    ds_pam["sfc_sif"] = (dim_2d, pam.p["sfc_sif"])
    ds_pam["sfc_sif"].attrs = dict(long_name="surface sea ice fraction")

    ds_pam["sfc_slf"] = (dim_2d, pam.p["sfc_slf"])
    ds_pam["sfc_slf"].attrs = dict(long_name="surface sea-land fraction")

    ds_pam["sfc_model"] = (dim_2d, pam.p["sfc_model"])
    ds_pam["sfc_model"].attrs = dict(long_name="surface model")

    ds_pam["sfc_refl"] = (dim_2d, np.array(pam.p["sfc_refl"].astype("str")))
    ds_pam["sfc_refl"].attrs = dict(long_name="surface reflection type")

    ds_pam["wind10u"] = (dim_2d, pam.p["wind10u"])
    ds_pam["wind10u"].attrs = dict(
        long_name="u-wind at 10 m height", units="m s^-1"
    )

    ds_pam["wind10v"] = (dim_2d, pam.p["wind10v"])
    ds_pam["wind10v"].attrs = dict(
        long_name="v-wind at 10 m height", units="m s^-1"
    )

    # atmospheric profile
    # ds_pam['hgt_lev'] = (dim_3d_lev, pam.p['hgt_lev'])
    # ds_pam['hgt_lev'].attrs = dict(long_name='height', units='m')

    # ds_pam['press_lev'] = (dim_3d_lev, pam.p['press_lev'])
    # ds_pam['press_lev'].attrs = dict(long_name='pressure', units='Pa')

    # ds_pam['temp_lev'] = (dim_3d_lev, pam.p['temp_lev'])
    # ds_pam['temp_lev'].attrs = dict(long_name='temperature', units='K')

    # ds_pam['relhum_lev'] = (dim_3d_lev, pam.p['relhum_lev'])
    # ds_pam['relhum_lev'].attrs = dict(long_name='relative humidity', units='%')

    # integrated profile variables
    ds_pam["iwv"] = (dim_2d, pam.p["iwv"])
    ds_pam["iwv"].attrs = dict(
        long_name="integrated water vapor", units="kg m^-2"
    )

    ds_pam["hydro_wp"] = (dim_3d_hydro, pam.p["hydro_wp"])
    ds_pam["hydro_wp"].attrs = dict(
        long_name="integrated hydrometeor content", units="kg m^-2"
    )

    # 3d variables
    ds_pam["obs_height"] = (dim_3d, pam.p["obs_height"])
    ds_pam["obs_height"].attrs = dict(
        long_name="observation height", units="m"
    )

    # 6d variables
    ds_pam["tb"] = (dim_6d, pam.r["tb"])
    ds_pam["tb"].attrs = dict(long_name="brightness temperature", units="K")

    # extend emissivity by upward angles
    emissivity = np.full(
        shape=[len(ds_pam[dim]) for dim in dim_5d], fill_value=np.nan
    )
    emissivity[..., ds_pam["angle"] > 90] = np.flip(
        pam.r["emissivity"], axis=[4]
    )
    ds_pam["emissivity"] = (dim_5d, emissivity)
    ds_pam["emissivity"].attrs = dict(
        long_name="emissivity", comment="defined for 180 > angle > 90"
    )

    # global attributes
    ds_pam.attrs = dict(
        title="PAMTRA model data",
        model=f'pyPamtra (Version: {pam.r["pamtraVersion"]}, '
        + f'Git Hash: {pam.r["pamtraHash"]})',
        pamtraVersion=pam.r["pamtraVersion"],
        author=f'{pam.nmlSet["creator"]} (University of Cologne, IGMK)',
        created=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        history="Created with pyPamtra and converted to xarray.Dataset under"
        + f" xarray version {xr.__version__}",
    )

    nml_keys = [
        "active",
        "passive",
        "add_obs_height_to_layer",
        "emissivity",
        "gas_mod",
        "outpol",
    ]
    ds_pam.attrs["pyPamtra_settings"] = ", ".join(
        [f"{key}: {str(pam.nmlSet[key])}" for key in nml_keys]
    )

    if split_angle:
        # split angle dimension into direction and incidence angle dimensions
        dir_expanded = np.array(["up", "down"], dtype="str").repeat(16)
        ang_expanded = np.append(
            ds_pam.angle.values[32:15:-1], ds_pam.angle.values[16:32]
        )
        ind = pd.MultiIndex.from_arrays(
            (dir_expanded, ang_expanded), names=("direction", "angle")
        )
        ds_pam = ds_pam.rename({"angle": "angle_180"})  # rename angle dim
        ds_pam = ds_pam.assign(angle_180=ind).unstack("angle_180")

        ds_pam["direction"].attrs = dict(
            long_name="direction of radiance",
            comment="up: upwelling radiance observed by down-looking "
            + "instrument, down: downwelling radiance observed by "
            + "up-looking instrument",
        )
        ds_pam["angle"].attrs = dict(
            long_name="incidence or zenith angle",
            comment="incidence (zenith) angle for direction=up(down) of the "
            + "radiance flux",
        )

        # simplify the data which is defined for some angles only
        ds_pam["emissivity"] = ds_pam["emissivity"].sel(direction="up")

    return ds_pam


class PamtraSurface:
    """
    Functions to set the PAMTRA surface properties.
    """

    def __init__(
        self,
        ds,
        kind,
        ocean_model="TESSEM2",
        ocean_refl="L",
        land_model="TELSEM2",
        land_refl="L",
        sea_ice_model="TELSEM2",
        sea_ice_refl="L",
    ):
        """
        Set the surface properties of PAMTRA profile. The PAMTRA profile is
        expected as xarray.Dataset

        Parameters
        -------
        ds: pamtra profile as xarray.Dataset
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

        self.set_sfc_type(kind=kind)

        self.set_sfc_model(
            ocean=ocean_model, land=land_model, sea_ice=sea_ice_model
        )

        self.set_sfc_refl(
            ocean=ocean_refl, land=land_refl, sea_ice=sea_ice_refl
        )

    def get_surface_mask(self, name):
        """
        Returns grid cells of a certain surface based on the area fractions.

        The decision is based on the 'sfc_slf' and 'sfc_sif' parameters:
          - sfc_slf: 0 = ocean, 1 = land
          - sfc_sif: 0 = ocean, 1 = sea ice

        Parameters
        ----------
        name: either 'ocean', 'land', or 'sea_ice'

        Returns
        -------
        A boolean mask with the indices where the surface is present
        """

        if name == "ocean":
            ix = (self.ds["sfc_slf"] < 0.5) & (self.ds["sfc_sif"] < 0.5)

        elif name == "land":
            ix = self.ds["sfc_slf"] > 0.5

        elif name == "sea_ice":
            ix = (self.ds["sfc_slf"] < 0.5) & (self.ds["sfc_sif"] > 0.5)

        else:
            ix = None

        return ix

    def set_sfc_type(self, kind="natural"):
        """
        Defines the PAMTRA surface type based on sea-land fraction and sea ice
        fraction

        PAMTRA surface types:
          0 = ocean
          1 = land/sea ice


        The classes are divided at 50% area fraction.

        Parameters
        -------
        kind: defines they way, surface types are identified. Either natural or
            idealized are possible. For idealized, a fixed emissivity is used
            for all surfaces. For natural, the emissivity is taken from one of
            the emissivity models.
        """

        assert kind in ["natural", "idealized"]

        # initialize surface type array
        self.ds["sfc_type"] = xr.full_like(self.ds["sfc_slf"], fill_value=0)

        if kind == "natural":
            # ocean
            self.ds["sfc_type"] = xr.where(
                self.get_surface_mask("land"), 1, self.ds["sfc_type"]
            )

            # land and sea ice
            self.ds["sfc_type"] = xr.where(
                self.get_surface_mask("land")
                | self.get_surface_mask("sea_ice"),
                1,
                self.ds["sfc_type"],
            )

        elif kind == "idealized":
            # pamtra will use the fixed emissivity
            self.ds["sfc_type"] = xr.full_like(
                self.ds["sfc_type"], fill_value=-9999
            )

    def set_sfc_model(
        self, ocean="TESSEM2", land="TELSEM2", sea_ice="TESSEM2"
    ):
        """
        Choose the surface model.

        For idealized emissivities for a certain surface type, set the surface
        type accordingly. (kind='idealized')

        Parameters
        -------
        ocean: surface model for ocean
        land: surface model for land
        sea_ice: surface model for sea ice
        """

        models = {
            "TESSEM2": 0,
            "FASTEM": 1,
            "TELSEM2": 0,
            "SSMI": 1,
        }

        # initialize surface model variable
        self.ds["sfc_model"] = xr.zeros_like(self.ds["sfc_type"])

        # select ocean model
        self.ds["sfc_model"] = xr.where(
            self.get_surface_mask("ocean"), models[ocean], self.ds["sfc_model"]
        )

        # select land model
        self.ds["sfc_model"] = xr.where(
            self.get_surface_mask("land"), models[land], self.ds["sfc_model"]
        )

        # select sea ice model
        self.ds["sfc_model"] = xr.where(
            self.get_surface_mask("sea_ice"),
            models[sea_ice],
            self.ds["sfc_model"],
        )

    def set_sfc_refl(self, ocean="F", land="F", sea_ice="F"):
        """
        Set surface reflection type for ocean, land, and sea ice.

        Possible parameters:
          F: Fresnel/Specular
          L: Lambertian

        Parameters
        -------
        ocean: reflection type over ocean
        land: reflection type over land
        sea_ice: reflection type over sea ice
        """

        # initialize the surface reflection field
        self.ds["sfc_refl"] = xr.full_like(
            self.ds["sfc_type"], fill_value="F", dtype="str"
        )

        # set reflection for ocean
        self.ds["sfc_refl"] = xr.where(
            self.get_surface_mask("ocean"), ocean, self.ds["sfc_refl"]
        )

        # set reflection for land
        self.ds["sfc_refl"] = xr.where(
            self.get_surface_mask("land"), land, self.ds["sfc_refl"]
        )

        # set reflection for sea ice
        self.ds["sfc_refl"] = xr.where(
            self.get_surface_mask("sea_ice"), sea_ice, self.ds["sfc_refl"]
        )
