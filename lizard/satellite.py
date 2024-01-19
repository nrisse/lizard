"""
Meta information for satellites:
- IFOV: instantaneous field of view in kilometers (along scan x along track)
  Values for across-track scanners (ATMS, MHS) are given only for nadir pixels.
  For AMSR2, the two 89 GHz scans have the same geometry and are therefore
  not distinguished here (channels 13 and 14 for the two 89 GHz polarizations)
  sources:
    - AMSR2: AMSR2 data users manual, page 16
    - SSMIS: Kunkee et al. (2008), page 866 (text)
    - ATMS: Kim et al. (2014), Figure 4 (only nadir here)
    - MHS: ATOVS Level 1b Product Guide (2010), page 19
"""

import cartopy.crs as ccrs
import numpy as np

from lizard.rt.polarization import scan_angle

# IFOV's for AMSR2, SSMIS, MHS (nadir), and ATMS (nadir). See sources above
IFOV = {
    "AMSR2": {
        1: [35, 62],
        2: [35, 62],
        3: [34, 58],
        4: [34, 58],
        5: [24, 42],
        6: [24, 42],
        7: [14, 22],
        8: [14, 22],
        9: [15, 26],
        10: [15, 26],
        11: [7, 12],
        12: [7, 12],
        13: [3, 5],
        14: [3, 5],
    },
    "SSMIS": {
        1: [17, 29],
        2: [17, 29],
        3: [17, 29],
        4: [17, 29],
        5: [17, 29],
        6: [16, 26],
        7: [16, 26],
        8: [9, 15],
        9: [9, 15],
        10: [9, 15],
        11: [9, 15],
        12: [44, 72],
        13: [44, 72],
        14: [44, 72],
        15: [26, 44],
        16: [26, 44],
        17: [9, 15],
        18: [9, 15],
        19: [16, 26],
        20: [16, 26],
        21: [16, 26],
        22: [16, 26],
        23: [16, 26],
        24: [16, 26],
    },
    "ATMS": {
        1: [74.8, 74.8],
        2: [74.8, 74.8],
        3: [31.6, 31.6],
        4: [31.6, 31.6],
        5: [31.6, 31.6],
        6: [31.6, 31.6],
        7: [31.6, 31.6],
        8: [31.6, 31.6],
        9: [31.6, 31.6],
        10: [31.6, 31.6],
        11: [31.6, 31.6],
        12: [31.6, 31.6],
        13: [31.6, 31.6],
        14: [31.6, 31.6],
        15: [31.6, 31.6],
        16: [31.6, 31.6],
        17: [15.8, 15.8],
        18: [15.8, 15.8],
        19: [15.8, 15.8],
        20: [15.8, 15.8],
        21: [15.8, 15.8],
        22: [15.8, 15.8],
    },
    "MHS": {
        1: [15.88, 15.88],
        2: [15.88, 15.88],
        3: [15.88, 15.88],
        4: [15.88, 15.88],
        5: [15.88, 15.88],
    },
}


# beam widths in degrees for ATMS and MHS. See sources above
BEAM_WIDTH = {
    "ATMS": {
        1: 5.2,
        2: 5.2,
        3: 2.2,
        4: 2.2,
        5: 2.2,
        6: 2.2,
        7: 2.2,
        8: 2.2,
        9: 2.2,
        10: 2.2,
        11: 2.2,
        12: 2.2,
        13: 2.2,
        14: 2.2,
        15: 2.2,
        16: 2.2,
        17: 1.1,
        18: 1.1,
        19: 1.1,
        20: 1.1,
        21: 1.1,
        22: 1.1,
    },
    "MHS": {
        1: 1.1,
        2: 1.1,
        3: 1.1,
        4: 1.1,
        5: 1.1,
    },
}


def ellipse_orientation(ssp, fpr, proj=None):
    """
    Computes orientation of footprint ellipse from sub-satellite point and
    footprint location at a given map projection.

    Parameters
    ----------
    ssp: sub-satellite point [lon, lat]
    fpr: footprint [lon, lat]
    proj: map projection

    Returns
    -------
    angle: orientation of the ellipse in the projected coordinate system
    """

    if proj is None:
        proj = ccrs.NorthPolarStereo()

    # project points to ECEF coordinates
    ssp_g = ccrs.Geocentric().transform_points(
        ccrs.Geodetic(), np.array([ssp[0]]), np.array([ssp[1]]), np.array([0])
    )
    fpr_g = ccrs.Geocentric().transform_points(
        ccrs.Geodetic(), np.array([fpr[0]]), np.array([fpr[1]]), np.array([0])
    )

    # get point very close to ellipse in direction of satellite
    fpp_g = fpr_g + (ssp_g - fpr_g) * 1e-2

    # convert points to map projection
    fpr_m = proj.transform_points(
        ccrs.Geocentric(), fpr_g[:, 0], fpr_g[:, 1], fpr_g[:, 2]
    )
    fpp_m = proj.transform_points(
        ccrs.Geocentric(), fpp_g[:, 0], fpp_g[:, 1], fpp_g[:, 2]
    )

    # compute angle of line that connects both points (footprint main axis)
    fpr_axis = fpp_m - fpr_m
    angle = np.rad2deg(np.arctan2(fpr_axis[0, 1], fpr_axis[0, 0]) + np.pi / 2)

    # ellipse position in map coordinates
    xy = (fpr_m[0, 0], fpr_m[0, 1])

    return [xy, angle]


def ifov(beam_width, incidence_angle, altitude):
    """
    Simplified computation of IFOV from satellite. Equation neglects Earth's
    curvature. Curvature is approximated by scaling the scan angle. This
    function is only meant for visualization and results should be checked.
    This function is only correct at nadir and more than 6% off at 60°
    incidence angle (for a thin beam of 1.1 degrees: 1-4 km).
    This is only valid for satellites near 833 km.
    Beams are generally wider and less high than real ones.

    This table shows real and computed ATMS footprints at nadir and off-nadir
    ifov(bw, 0, 833) and ifov(bw, 64, 833) for different beam widths
    real - computed for 0 deg | 64 deg incidence angle
    5.2 deg: 74.8 - 75.7 | 323.1, 141.8 - 304.7, 151.4
    2.2 deg: 31.6 - 32.0 | 136.7, 60.0 - 128.2, 64.0
    1.1 deg: 15.8 - 16.0 | 68.4, 30.0 - 64.0, 32.0

    Improvements: Approximate Earth curvature more realistically considering
    the flight altitude.

    Parameters
    ----------
    beam_width: channel beam width in degrees
    incidence_angle: incidence angle at Earth's surface in degrees
    altitude: satellite altitude in km

    Returns
    -------
    width: ellipse width at surface
    height: ellipse height at surface
    """

    # compute scan angle from incidence angle
    scan_ang = scan_angle(altitude * 1e3, incidence_angle)

    # scale scan angle to account curvature of Earth (only for visualization)
    angle_ = scan_ang * 1.14

    # convert angles to radiance
    angle = np.deg2rad(angle_)
    beam_width = np.deg2rad(beam_width)

    # compute length of line of sight
    line_of_sight_range = altitude / np.cos(angle)
    width = 2 * line_of_sight_range * np.tan(beam_width / 2)

    height = altitude * (
        np.tan(angle + beam_width / 2) - np.tan(angle - beam_width / 2)
    )

    return width, height
