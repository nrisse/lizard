"""
Read and write bit flags with xarray.
"""

import numpy as np


def pack_bit_mask(boolean_mask):
    """
    Creates uint8 flag array from up to eight boolean masks.

    Parameters
    -------
    boolean_mask: individual masks to be converted to uint8 flag. The shape
    is (n_features, ...)

    Returns
    -------
    bit_mask: uint8 bit values.
    """

    shape = list(boolean_mask.shape)
    shape[0] = 8
    mask = np.zeros(shape, dtype="uint8")
    mask[: boolean_mask.shape[0], ...] = boolean_mask
    bit_mask = np.packbits(mask, axis=0, bitorder="little")[0, ...]

    return bit_mask


def unpack_bit_mask(bit_mask):
    """


    Parameters
    ----------
    bit_mask: uint8 bit values.

    Returns
    -------
    boolean_mask: boolean mask with features in rows and samples in columns
    """

    boolean_mask = np.unpackbits(
        bit_mask[np.newaxis, ...], axis=0, bitorder="little"
    )

    return boolean_mask


def write_flag_xarray(ds, bool_vars, bool_meanings, bit_mask_name, drop=True):
    """
    Write bit flag from xarray. Adds flag values and flag meanings attributes
    as specified.

    Parameters
    ----------
    ds: xarray Dataset that contains the boolean masks
    bool_vars: variable names to be converted to bit mask (uint8, 0 or 1)
    bool_meanings: meaningful variable name that is added as attribute
    bit_mask_name: variable name of bit mask
    drop: whether to remove the boolean masks from the dataset

    Returns
    -------
    xarray Dataset with bit mask
    """

    bit_mask_values = pack_bit_mask(ds[bool_vars].to_array().values)
    ds[bit_mask_name] = (ds[bool_vars[0]].dims, bit_mask_values)
    ds[bit_mask_name].attrs["flag_meanings"] = " ".join(bool_meanings)
    ds[bit_mask_name].attrs["flag_masks"] = 2 ** np.arange(
        len(bool_meanings), dtype="uint8"
    )

    if drop:
        ds = ds.drop(bool_vars)

    return ds


def read_flag_xarray(ds, bit_mask_name="surf_type", drop=True):
    """
    Read bit flag from xarray into individual arrays using flag_masks and
    flag_meanings attributes.

    Assumes that flag_masks are unique and sorted bits.

    Parameters
    ----------
    ds: xarray Dataset with bit mask
    bit_mask_name: name of bit mask
    drop: whether to drop the bit mask

    Returns
    -------
    xarray Dataset with boolean flags from the flag_meanings stored as
    attributes.
    """

    flag_meanings = ds[bit_mask_name].attrs["flag_meanings"].split(" ")
    # flag_masks = ds[bit_mask_name].attrs['flag_masks']
    boolean_mask = unpack_bit_mask(ds[bit_mask_name].values)

    for i, flag_meaning in enumerate(flag_meanings):
        ds[flag_meaning] = (ds[bit_mask_name].dims, boolean_mask[i, ...])

    # remove bit mask
    if drop:
        ds = ds.drop(bit_mask_name)

    return ds
