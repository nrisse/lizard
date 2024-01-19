"""
Write xarray dataset to shapefile
"""

import geopandas as gpd


def xarray2shapefile(ds, file, coords=('lon', 'lat'), epsg='4326'):
    """
    Writes xarray datset to shapefile.

    Parameters
    ----------
    ds: xarray Dataset or DataArray.
    coords: x and y coordinates.
    epsg: epsg code of coordinates
    """

    df = ds.to_dataframe().reset_index()

    if 'time' in list(df):
        df['time'] = df['time'].astype('str')

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[coords[0]], df[coords[1]]),
        crs=f'EPSG:{epsg}')

    gdf.to_file(file)
