"""
Reads land shapefile from Norwegian Polar Institute to Geopandas.
"""


import os

import geopandas


def read_land():
    """
    Reads land shapefile from Norwegian Polar Institute to Geopandas.

    Returns
    -------
    Geopandas DataFrame that contains land polygons of Svalbard.
    """

    gdf = geopandas.GeoDataFrame.from_file(
        os.path.join(
            os.environ["PATH_SEC"],
            "data/land_cover/NP_S100_SHP/S100_Land_f.shp",
        )
    )

    return gdf


def read_glaciers():
    """
    Reads glacier shapefile from Norwegian Polar Institute to Geopandas.

    Returns
    -------
    Geopandas DataFrame that contains glacier polygons of Svalbard.
    """

    gdf = geopandas.GeoDataFrame.from_file(
        os.path.join(
            os.environ["PATH_SEC"],
            "data/land_cover/NP_S100_SHP/S100_Isbreer_f.shp",
        )
    )

    return gdf


def read_land_crt(crs):
    """
    Reads land shapefile and reprojects it to a cartopy projection.

    Returns
    -------
    Geopandas DataFrame that contains land polygons of Svalbard reprojected to
    a cartopy projection
    """

    return read_land().to_crs(crs.proj4_init)


def read_glaciers_crt(crs):
    """
    Reads glacier shapefile and reprojects it to a cartopy projection.

    Returns
    -------
    Geopandas DataFrame that contains land polygons of Svalbard reprojected to
    a cartopy projection
    """

    return read_glaciers().to_crs(crs.proj4_init)
