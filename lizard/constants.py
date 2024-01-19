"""
Dataclass with constants
"""

from dataclasses import dataclass


@dataclass
class Constants:
    """
    Various constants for meteorological equations
    """

    molar_mass_dry_air = 28.9647e-3  # kg/mol
    molar_mass_water_vapor = 18.01528e-3  # kg/mol
