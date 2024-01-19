"""
Provides a unified data structure to import channel information of airborne
(not yet implemented) and space-borne passive microwave radiometers.
Reads filter files from RTTOV V13 based on an input of instrument and for
SSMIS also the satellite. The same filter files will be built for the airborne
instruments.

Description from https://nwp-saf.eumetsat.int/site/software/rttov/download/ \
coefficients/spectral-response-functions/
---
Key for MW pass band filter files:
  Two records for each channel
  Fields in record 1: channel, polarisation, no-of-offsets, bandwidth (MHz)
  Fields in record 2: central frequency (GHz), offset1 (GHz), offset2 (GHz)

  Notes
  (1) Polarisation - this refers to the treatment of surface emissivity:
         0: Average of vertical and horizontal polarisation i.e. 0.5(H+V)
         1: Nominal vertical at nadir rotating with view angle QV
         2: Nominal horizontal at nadir rotating with view angle QH
         3: Vertical V
         4: Horizontal H
         5: +45 minus -45 (3rd stokes vector) S3
         6: Left circular - right circular (4th stokes vector) S4
         7: Uneven, fixed, channel-specific mixture of V and H

  (2) no-of-offsets
         0: one passband channel
         1: two sideband channel
         2: four sideband channel

  (3) Bandwidth is for each passband
---
"""


import os

import numpy as np
import xarray as xr
from dotenv import load_dotenv

load_dotenv()


ACRONYM = {
    "AltiKa": "altika",
    "AMR": "amr",
    "AMR-C": "amrc",
    "AMSR2": "amsr2",
    "AMSR-E": "amsre",
    "AMSU-A": "amsua",
    "AMSU-B": "amsub",
    "ATMS": "atms",
    "AWS": "aws",
    "COWVR": "cowvr",
    "CPR": "cpr",
    "DPR": "dpr",
    "ESMR": {
        "Nimbus-5": "esmr_n5",
        "Nimbus-6": "esmr_n6",
    },
    "GMI": "gmi",
    "HSB": "hsb",
    "MWRI": {
        "HY-2A": "hy2mwri",
        "HY-2B": "hy2mwri",
        "FY-3A": "mwri",
        "FY-3B": "mwri",
        "FY-3C": "mwri",
        "FY-3D": "mwri",
        "FY-3F": "mwri",
        "FY-3H": "mwri",
    },
    "ICI": "ici",
    "MADRAS": "madras",
    "MHS": "mhs",
    "MIRAS": "miras",
    "MSU": "msu",
    "MTVZA-GY": "mtvzagy",
    "MWHS-1": "mwhs",
    "MWHS-2": "mwhs2",
    "MWI": "mwi",
    "MWR": "mwr",
    "MWS": "mws",
    "MWTS-1": "mwts",
    "MWTS-2": "mwts2",
    "NEMS": "nems",
    "POLSIR": "polsir",
    "SAPHIR": "saphir",
    "SCAMS": "scams",
    "SMMR": "smmr",
    "SSM/I": "ssmi",
    "SSMIS": {
        "DMSP-F16": "ssmis-dmsp16only",
        "DMSP-F17": "ssmis-notdmsp16",
        "DMSP-F18": "ssmis-notdmsp16",
        "DMSP-F19": "ssmis-notdmsp16",
    },
    "SSM/T-2": "ssmt2",
    "TMI": "tmi",
    "TMS": "tropics",
    "WindSat": "windsat",
    "MiRAC-A": "miraca",
    "MiRAC-P": "miracp",
    "HATPRO": "hatpro",
    "HAMP": "hamp",
}


POL_MEANING = {
    0: "VH",
    1: "QV",
    2: "QH",
    3: "V",
    4: "H",
    5: "S3",
    6: "S4",
    7: "xVH",
}


def read_band_pass(
    instrument, satellite="unspecified", calc_avg=True, add_labels=True
):
    """
    Read RTTOV coefficient file for a given instrument. The configuration of
    some instruments differs between satellites (i.e., SSMIS, MWRI, ESMR).
    For these, the satellite should be given as well.

    Example:
    read_band_pass('SSMIS', 'DMSP-F18')

    Parameters
    ----------
    instrument: microwave instrument acronym as given in WMO/OSCAR database.
    satellite: satellite acronym as given in WMO/OSCAR database.
    calc_avg: whether to calculate the four averaging frequencies.
    add_labels: whether to add string labels for each channel.

    Returns
    -------
    xarray.Dataset of the instrument band pass data.
    """

    # get rttov acronym
    acronym = ACRONYM[instrument]
    if type(acronym) == dict:
        acronym = ACRONYM[instrument][satellite]

    # read file
    file = os.path.join(
        os.environ["PATH_SEC"],
        f"data/sat/mw_overview/filter_files/{acronym}.flt",
    )

    pass_band = {}
    empty_channel = dict(
        polarization="",
        n_if_offsets="",
        bandwidth="",
        center_freq="",
        if_offset_1="",
        if_offset_2="",
    )

    with open(file, "r") as f:
        i = 0
        for line in f.readlines():
            if line == "\n":
                continue

            elif i % 2 == 0:
                line_elements = line.split()

                ch = int(line_elements[0])

                # create empty channel
                pass_band[ch] = empty_channel.copy()
                pass_band[ch]["polarization"] = int(line_elements[1])
                pass_band[ch]["n_if_offsets"] = int(line_elements[2])
                pass_band[ch]["bandwidth"] = float(line_elements[3])

                i += 1

            else:
                line_elements = line.split()

                pass_band[ch]["center_freq"] = float(line_elements[0])

                if len(line_elements) > 1:
                    pass_band[ch]["if_offset_1"] = float(line_elements[1])

                else:
                    pass_band[ch]["if_offset_1"] = 0

                if len(line_elements) > 2:
                    pass_band[ch]["if_offset_2"] = float(line_elements[2])

                else:
                    pass_band[ch]["if_offset_2"] = 0

                i += 1

    # change data types from string to int/float
    ds = xr.Dataset()
    ds.coords["channel"] = list(pass_band.keys())
    for x in empty_channel.keys():
        ds[x] = ("channel", [pass_band[ch][x] for ch in ds.channel.values])

    # add attributes
    ds.attrs = dict(
        title="Pass band data for MW coefficient files",
        instrument=instrument,
        platform=satellite,
        history="Created from RTTOV MW coefficient files",
        citation="source: https://nwp-saf.eumetsat.int/site/software/rttov/"
        + "download/coefficients/spectral-response-functions/",
    )

    ds["channel"].attrs = dict(long_name="channel number")
    ds["center_freq"].attrs = dict(
        units="GHz", description="Center frequency of the channel"
    )
    ds["polarization"].attrs = dict(
        standard_name="polarization",
        long_name="polarization",
        description="Polarization of the channel",
        flag_meanings="average_vertical_horizontal "
        "nominal_vertical_at_nadir_rotating "
        "nominal_horizontal_at_nadir_rotating "
        "vertical "
        "horizontal "
        "+45_minus_-45 "
        "left_circular_minus_right_circular "
        "uneven_mixture",
        flag_values=[0, 1, 2, 3, 4, 5, 6, 7],
    )
    ds["n_if_offsets"].attrs = dict(
        long_name="Number of intermediate frequency offsets",
        description="0: one freq; 1: two freq; 2: four freq",
    )
    ds["bandwidth"].attrs = dict(
        long_name="bandwidth",
        standard_name="bandwidth",
        units="MHz",
        description="Bandwith of each averaging frequency",
    )
    ds["if_offset_1"].attrs = dict(
        long_name="first intermediate frequency offset",
        standard_name="first_intermediate_frequency_offset",
        units="GHz",
        description="Offset of first intermediate frequency stage",
    )
    ds["if_offset_2"].attrs = dict(
        long_name="second intermediate frequency offset",
        standard_name="second_intermediate_frequency_offset",
        units="GHz",
        description="Offset of second intermediate frequency stage",
    )

    # calculate averaging frequencies
    if calc_avg:
        ds = calc_avg_freq(ds)

    # add labels
    if add_labels:
        ds = create_labels(ds)

    return ds


def read_band_pass_combination(sensor1="MiRAC-A", sensor2="MiRAC-P"):
    """
    Creates one band pass dataset for two instruments, e.g. MiRAC-A and
    MiRAC-P, that are flown on the same platform.

    Returns
    -------
    xr.Dataset of band pass data.
    """

    ds_bp_s1 = read_band_pass(sensor1)
    ds_bp_s2 = read_band_pass(sensor2)

    ds_bp_s2["channel"] = ds_bp_s2["channel"] + len(ds_bp_s1["channel"])

    ds = xr.concat([ds_bp_s1, ds_bp_s2], dim="channel")
    ds.attrs["instrument"] = f"{sensor1} and {sensor2}"

    return ds


def calc_avg_freq(ds):
    """
    Calculate averaging frequencies for every channel based on the
    specified intermediate frequencies. Four frequencies are given always,
    to allow a common data structure among the different channels.

    Input
    -------
    ds: xarray.Dataset of instrument

    Returns
    -------
    avg_freq : np.ndarray
        Numpy array with the averaging frequencies for each channel. If
        only one averaging frequency occurs, i.e., if_offset is zero, the
        frequency will occur four times to ensure common dimensions
        between the channels.
    """

    ds.coords["n_avg_freq"] = [1, 2, 3, 4]
    ds["avg_freq"] = (
        ("channel", "n_avg_freq"),
        np.zeros((len(ds.channel), 4)),
    )

    ds["avg_freq"][:, 0] = ds.center_freq - ds.if_offset_1 - ds.if_offset_2
    ds["avg_freq"][:, 1] = ds.center_freq - ds.if_offset_1 + ds.if_offset_2
    ds["avg_freq"][:, 2] = ds.center_freq + ds.if_offset_1 - ds.if_offset_2
    ds["avg_freq"][:, 3] = ds.center_freq + ds.if_offset_1 + ds.if_offset_2

    ds.coords["n_avg_freq"].attrs = dict(
        description="Enumerating the frequencies, which are averaged."
    )
    ds["avg_freq"].attrs = dict(
        units="GHz",
        description="Frequencies, which are averaged.",
    )

    return ds


def create_labels(ds):
    """
    Creates string that described channel frequencies.

    Parameters
    ----------
    ds: band pass dataset.

    Returns
    -------
    labels: list of labels
    """

    labels = []
    labels_pol = []
    for channel in ds.channel:
        n = ds.n_if_offsets.sel(channel=channel).item()
        c = ds.center_freq.sel(channel=channel).item()
        o1 = ds.if_offset_1.sel(channel=channel).item()
        o2 = ds.if_offset_2.sel(channel=channel).item()
        p = POL_MEANING[ds.polarization.sel(channel=channel).item()]

        if n == 0:
            label = r"%g GHz" % c
        elif n == 1:
            label = r"%g$\pm$%g GHz" % (c, o1)
        elif n == 2:
            label = r"%g$\pm$%g$\pm$%g GHz" % (c, o1, o2)
        else:
            label = ""
            print(f"Warning: n_if_offsets of ch{channel} not in [0, 1, 2].")

        labels.append(label)
        labels_pol.append(label.replace("GHz", f"({p}) GHz"))

    ds["label"] = ("channel", labels)
    ds["label_pol"] = ("channel", labels_pol)
    ds["label"].attrs = dict(description="String label of channel")
    ds["label_pol"].attrs = dict(
        description="String label of channel with " "polarization."
    )

    return ds
