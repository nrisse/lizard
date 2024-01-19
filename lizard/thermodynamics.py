"""
Conversions of meteorological quantities
"""

import numpy as np

from lizard.constants import Constants


def mol2q(water_vapor_molecular_density, air_molecular_density):
    """
    Molecular density of water vapor to specific humidity.

    specific humidity = mass water vapor / (mass dry air + mass water vapor)

    Parameters
    ----------
    water_vapor_molecular_density: 1/m3
        Molecular density of water vapor
    air_molecular_density: 1/m3
        Molecular density of air (dry air + water vapor)

    Returns
    -------
    specific_humidity: kg/kg
        Specific humidity
    """

    dry_air_molecular_density = (
        air_molecular_density - water_vapor_molecular_density
    )

    specific_humidity = (
        water_vapor_molecular_density
        * Constants.molar_mass_water_vapor
        / (
            dry_air_molecular_density * Constants.molar_mass_dry_air
            + water_vapor_molecular_density * Constants.molar_mass_water_vapor
        )
    )

    return specific_humidity


def calculate_iwv(ds, p_var, t_var, rh_var, z_var):
    """
    Calculate iwv from RH, temperature, pressure, and altitude.

    Parameters
    ----------
    ds: xarray dataset that contains all variables
    p_var: pressure variable name. pressure in hPa
    t_var: temperature variable name. temperature in K
    rh_var: relative humidity variable name. rh in percent
    z_var: height variable name. height in m
    """

    # calculate mixing ratio [kg/kg]
    ds["qv"] = calculate_qv(p=ds[p_var], t=ds[t_var], rh=ds[rh_var] * 0.01)

    # calculate air sensity [kg/m3]
    ds["rho"] = calculate_air_density(p=ds[p_var], t=ds[t_var], qv=ds["qv"])

    # calculate absolute humidity [kg/m3]
    ds["abs_hum"] = ds["rho"] * ds["qv"]

    # integrate vertically [kg/m2]
    ds["iwv"] = (ds["abs_hum"] * ds[z_var].diff(z_var)).sum(z_var)

    return ds


def esat_equation(T):
    """
    Result will be in Pa
    """

    e_sat = (
        100
        * 1013.246
        * 10
        ** (
            -7.90298 * (373.16 / T - 1)
            + 5.02808 * np.log10(373.16 / T)
            - 1.3816e-7 * (10 ** (11.344 * (1 - T / 373.16)) - 1)
            + 8.1328e-3 * (10 ** (-3.49149 * (373.16 / T - 1)) - 1)
        )
    )

    return e_sat


def calculate_qv(p, t, rh):
    """
    Mixing ratio
    """

    eps = 18 / 28.96

    e_sat = esat_equation(t)

    e = rh * e_sat

    # convert pressure from hpa to pa
    p = p * 100

    q = eps * e / (p - e + eps * e)

    return q


def q2rh(q, p, t):
    """
    Mixing ratio to relative humidity
    """

    eps = 18 / 28.96

    e_sat = esat_equation(t)

    e = q * (p - e_sat) / (eps + q)

    rh = e / e_sat

    return rh


def calculate_air_density(p, t, qv):
    """
    Air density
    """

    Rd = 287  # J/kg K
    Tv = t * (1 + 0.61 * qv)

    rho = (p * 100) / (Rd * Tv)

    return rho
