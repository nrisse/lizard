"""
This function helps to get an overview over variables and coordinates of large
xarray.Datasets such as model fields or observations. It returns a data frame
of with dimension and shape for each coordinate/variable.
"""


import pandas as pd


def dataset_to_table(ds):
    """
    Creates a table of all variables and coordinates of an xarray.Dataset and
    their dimension and shape .

    Parameters
    ----------
    ds: xarray.Dataset, that gets converted into a list view.

    Returns
    -------
    pd.DataFrame with the xarray.Dataset coordinates and variables.
    """

    ds_dct = ds.to_dict(data=False)
    df_dct = dict(kind=[], name=[], dims=[], shape=[])

    for kind in ["coords", "data_vars"]:
        for name in ds_dct[kind].keys():
            df_dct["kind"].append(kind)
            df_dct["name"].append(name)
            df_dct["dims"].append(ds_dct[kind][name]["dims"])
            df_dct["shape"].append(ds_dct[kind][name]["shape"])

    df = pd.DataFrame.from_dict(df_dct)

    return df
