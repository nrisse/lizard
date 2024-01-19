"""
Distance calculator.
"""


import cartopy.crs as ccrs
import numpy as np


def distance(lat, lon, lat0, lon0, lat1, lon1, utm=None, epsg=None):
    """
    Calculates the distance between the points lat/lon and lat0/lon0 projected
    along the straight line connecting the points lat0/lon0 and lat1/lon1.
    lat0/lon0 is set as origin with positive values towards lat1/lon0 and
    negative values in the opposite direction.

    A projected coordinate system has to be specified as EPSG code

    Parameters
    ----------
    lat : int or np.array
        Latitude of point for which distance will be calculated.
    lon : int or np.array
        Longitude of point for which distance will be calculated.
    lat0 : int
        Latitude origin point.
    lon0 : int
        Longitude origin point.
    lat1 : int
        Latitude end point.
    lon1 : int
        Longitude end point.
    utm : str, optional
        UTM zone. The default is 32 (valid from 6 to 12 deg E).

    Returns
    -------
    d_p1_p1 : int or np.array
        Distance in meters within the projected coordinate system.
    """

    assert epsg is None or utm is None

    # define coordinate systems
    if epsg is None:
        cs_proj = ccrs.UTM(zone=utm)

    else:
        cs_proj = ccrs.epsg(epsg)

    cs_geog = ccrs.PlateCarree()

    # start and end points of track
    p0 = np.array([[lon0], [lat0]])
    p1 = np.array([[lon1], [lat1]])

    # project all coordinates to (x, y, z)
    p0_p = cs_proj.transform_points(x=p0[0, :], y=p0[1, :], src_crs=cs_geog)
    p1_p = cs_proj.transform_points(x=p1[0, :], y=p1[1, :], src_crs=cs_geog)
    pn_p = cs_proj.transform_points(x=lon, y=lat, src_crs=cs_geog)

    # calculate unit vector along track
    e_d = (p1_p - p0_p) / np.linalg.norm(p1_p - p0_p, axis=1)

    # project vector from start point to target points along axis of track
    dist = np.dot((pn_p - p0_p), e_d.T)[..., 0]

    return dist
