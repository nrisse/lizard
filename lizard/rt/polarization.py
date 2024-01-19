"""
Conversion from horizontal and vertical polarization observed by SSMIS/AMSR2
to mixed polarization observed by ATMS/MHS
"""

import numpy as np


def scan_angle(alt, incidence_angle, angle_deg=True):
    """
    Calculate scan angle from platform altitude and incidence angle

    Parameters
    ----------
    alt: platform flight altitude
    incidence_angle: local incidence angle at Earth's surface
    angle_deg: angle unit in degrees

    """

    if angle_deg:
        incidence_angle = np.deg2rad(incidence_angle)

    re = 6371000  # mean earth radius

    scan_ang = np.arcsin(re / (re + alt) * np.sin(incidence_angle))

    if angle_deg:
        scan_ang = np.rad2deg(scan_ang)

    return scan_ang


def vh2qv(v, h, incidence_angle, alt, angle_deg=True):
    """

    Parameters
    ----------
    v: vertically-polarized radiation
    h: horizontally-polarized radiation
    incidence_angle: incidence angle
    alt: platform flight altitude
    angle_deg: angle unit in degrees

    Returns
    -------
    QV-polarized radiance
    """

    if angle_deg:
        incidence_angle = np.deg2rad(incidence_angle)

    scan_ang = scan_angle(alt, incidence_angle, angle_deg=angle_deg)

    x = v * np.cos(scan_ang) ** 2 + h * np.sin(scan_ang) ** 2

    return x


def vh2qh(v, h, incidence_angle, alt, angle_deg=True):
    """

    Parameters
    ----------
    v: vertically-polarized radiation
    h: horizontally-polarized radiation
    incidence_angle: incidence angle
    alt: platform flight altitude
    angle_deg: angle unit in degrees

    Returns
    -------
    QH-polarized radiance
    """

    if angle_deg:
        incidence_angle = np.deg2rad(incidence_angle)

    scan_ang = scan_angle(alt, incidence_angle, angle_deg=angle_deg)

    x = h * np.cos(scan_ang) ** 2 + v * np.sin(scan_ang) ** 2

    return x


def pamtra2instrument(
    ds_pam, polarization, incidence_angle, altitude, is_satellite=True
):
    """
    Convert PAMTRA output to observation of specific instrument

    Parameters
    ----------
    ds_pam: pamtra simulation with tb as a function of at least polarization,
      angle, and obs_height
    polarization: string of polarization type (V, H, QV, QH)
    incidence_angle: incidence angle at the surface
    altitude: platform altitude
    is_satellite: if the instrument is on satellite, the tb simulated with
      PAMTRA is extracted at 833 km. For mixed polarizations, however, the
      actual satellite flight altitude is used to compute the scan angle.

    Returns
    -------
    da_tb: tb DataArray with TB as observed by the instrument
    """

    pol_conv = {"QV": vh2qv, "QH": vh2qh}

    incidence_angle = np.abs(incidence_angle)

    if is_satellite:
        da_tb = ds_pam.tb.sel(obs_height=833000).interp(angle=incidence_angle)
    else:
        da_tb = ds_pam.tb.interp(obs_height=altitude, angle=incidence_angle)

    if polarization in ["V", "H"]:
        da_tb = da_tb.sel(polarization=polarization)

    elif polarization in ["QV", "QH"]:
        da_tb = pol_conv[polarization](
            v=da_tb.sel(polarization="V"),
            h=da_tb.sel(polarization="H"),
            incidence_angle=incidence_angle,
            alt=altitude,
        ).rename("tb")

    else:
        raise "Polarization must be one of [V, H, QV, QH]"

    return da_tb
