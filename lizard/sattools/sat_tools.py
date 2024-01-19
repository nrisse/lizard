"""
Collection of useful tools which make work with microwave satellite data more
efficient

Included tools:
    - list of MW instruments per satellite
    - satellites, on which MW instrument is carried
"""


import os

import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class OSCAR:
    """
    Provides simple reading and filtering of satellite databased from
    WMO/OSCAR. Currently, these tables are supported:

    https://space.oscar.wmo.int/satelliteprogrammes
    https://space.oscar.wmo.int/satellites
    https://space.oscar.wmo.int/instruments
    https://space.oscar.wmo.int/satellitefrequencies (Earth observation MW
                                                      frequencies)

    No filtering was applied on the downloaded .xlsx sheets to provide all
    the information here. The following information is provided in each of the
    four tables:

    satellite programmes:
        Id, Acronym, Name, Start of Programme, End of Programme, Agencies,
        Satellites

    satellites:
        Acronym, SAT ID, Launch, (expected) EOL, Satellite Programme, Agencies,
        Orbit, Altitude, Longitude, Inclination, Ect, Sat status, Payload,
        Last update

    instruments:
        Id, Acronym, Full name, Space Agency, Instrument type, Satellites,
        Usage from, Usage to, Last update

    satelite frequencies:
        Id, Satellite, Space Agency, Launch, Eol, Service, Sensing mode,
        Frequency (GHz), Bandwidth (MHz), Polarisation, Comment
    """

    space_agencies = ["NASA", "DoD", "NOAA", "JAXA", "ESA", "EUMETSAT", "CNES"]

    def __init__(self):
        """
        Reads OSCAR databases and performs basic corrections
        """

        self.pro = self.read("oscar_satelliteprogrammes.xlsx")
        self.sat = self.read("oscar_satellites.xlsx")
        self.ins = self.read("oscar_instruments.xlsx")
        self.fre = self.read("oscar_satellite_frequencies_eo_mw.xlsx")

        self.to_numeric()
        self.to_list()
        self.correct_names()

    @staticmethod
    def read(table):
        """Read specific database and rename columns"""

        df = pd.read_excel(
            os.path.join(os.environ["PATH_SAT"], "mw_overview", table),
            dtype="str",
        )

        df = df.rename(
            columns={
                colname: colname.strip()
                .replace("(", "")
                .replace(")", "")
                .replace(" ", "_")
                .lower()
                for colname in df.columns
            }
        )

        for c in df.columns:
            df[c] = df[c].str.strip()

        return df

    def to_numeric(self):
        """Convert columns to numeric"""

        self.fre["freq_num"] = np.array(
            [
                f.split(" GHz")[0].split(" - ")[0]
                for f in self.fre["frequency_ghz"]
            ],
            dtype="float",
        )

        self.fre["launch_num"] = pd.to_datetime(
            np.array([str(s).replace("≥", "") for s in self.fre["launch"]])
        )

        self.fre["eol_num"] = pd.to_datetime(
            np.array([str(s).replace("≥", "") for s in self.fre["eol"]])
        )

    def to_list(self):
        """Convert payload and satellites to list"""

        self.sat["payload"] = self.sat["payload"].fillna("")
        self.sat["payload"] = self.sat["payload"].apply(
            lambda row: row.split("\n")
        )

        self.ins["satellites"] = self.ins["satellites"].fillna("")
        self.ins["satellites"] = self.ins["satellites"].apply(
            lambda row: row.split("\n")
        )

    def correct_names(self):
        """
        AMSR2 is written AMSR-2 in the frequency list
        """

        self.fre.loc[self.fre.service == "AMSR-2", "service"] = "AMSR2"

    def only_space_agencies(self, space_agencies):
        """Reduce to a list of space agencies"""

        self.fre = self.fre[np.isin(self.fre["space_agency"], space_agencies)]

    def only_passive(self):
        """Keep only passive instruments"""

        self.fre = self.fre[self.fre["sensing_mode"] == "passive"]

    def only_sunsync(self):
        """Keep only frequencies of instruments in polar orbit"""

        # get list of sun-synchroneous satellites
        sat_sunsynch = self.sat.loc[self.sat["orbit"] == "SunSync", "acronym"]

        # reduce to listed satellites
        self.fre = self.fre.loc[
            np.isin(self.fre["satellite"], sat_sunsynch), :
        ]

    def no_limb(self):
        """Remove limb sounders from frequencies"""

        limb = self.ins.loc[
            self.ins.instrument_type == "Limb sounder", "acronym"
        ]
        self.fre = self.fre.loc[~np.isin(self.fre.service, limb), :]

    def within_available(self, t0, t1):
        """Return frequencies available within a certain time period"""

        return self.fre.loc[
            ((self.fre["launch_num"] < t1) & (self.fre["eol_num"] > t0)), :
        ]

    def within_available_fully(self, t0, t1):
        """
        Select only frequencies available within time period, i.e., launched
        before and eol after period.
        """

        return self.fre.loc[
            ((self.fre["launch_num"] < t0) & (self.fre["eol_num"] > t1)), :
        ]

    def drop_instruments(self, drop=[]):
        """
        Drop specific list of instruments
        """

        drop_default = [
            "Coriolis",
            "Sentinel-3A",
            "Sentinel-3B",
            "SMOS",
            "SARAL",
        ]

        if drop == []:
            self.fre = self.fre.loc[
                ~np.isin(self.fre.satellite, drop_default), :
            ]
        else:
            self.fre = self.fre.loc[~np.isin(self.fre.satellite, drop), :]

    def within_available_partly(self, t0, t1):
        """
        Select only frequencies available within time period.
        1: launch before and eol within period
        2: launch within period
        """

        return self.fre.loc[
            (
                (self.fre["launch_num"] < t0)
                & (self.fre["eol_num"] > t0)
                & (self.fre["eol_num"] < t1)
            )
            | ((self.fre["launch_num"] > t0) & (self.fre["launch_num"] < t1)),
            :,
        ]

    def payload_of_satellites(self, sat_list):
        """
        Create dictionary with payload given a list of satellite names
        """

        dct = dict()

        for sat in sat_list:
            dct[sat] = self.sat.loc[self.sat.acronym == sat, "payload"].item()

        return dct

    def satellites_of_instrument(self, instr_list):
        """
        Get satellites which carry the instrument
        """

        dct = dict()

        for inst in instr_list:
            dct[inst] = self.ins.loc[
                self.ins.acronym == inst, "satellites"
            ].item()

        return dct


if __name__ == "__main__":
    osc = OSCAR()

    osc.only_passive()
    osc.only_space_agencies(osc.space_agencies)
    osc.only_sunsync()
    osc.no_limb()
    osc.drop_instruments()

    fre = osc.within_available(
        np.datetime64("2017-01-01"), np.datetime64("2022-08-30")
    )

    fre.satellite.unique()

    len(fre.satellite.unique())

    dct1 = osc.payload_of_satellites(fre.satellite.unique())
    dct2 = osc.satellites_of_instrument(fre.service.unique())
