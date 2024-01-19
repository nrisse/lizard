"""
Planning of the comparison between satellite and field campaigns

This includes an overview of all operational microwave satellites during the
campaign periods
"""


import datetime

import numpy as np
from dotenv import load_dotenv
from sat_tools import OSCAR

load_dotenv()


# campaign periods as additional information
missions = {
    "ACLOUD": (datetime.datetime(2017, 5, 23), datetime.datetime(2017, 6, 26)),
    "AFLUX": (datetime.datetime(2019, 3, 19), datetime.datetime(2019, 4, 11)),
    "MOSAiC-ACA": (
        datetime.datetime(2020, 8, 30),
        datetime.datetime(2020, 9, 13),
    ),
    "HALO-AC3": (
        datetime.datetime(2022, 3, 12),
        datetime.datetime(2022, 4, 12),
    ),
    "WALSEMA": (
        datetime.datetime(2022, 6, 27),
        datetime.datetime(2022, 8, 16),
    ),
}


if __name__ == "__main__":
    osc = OSCAR()

    print(list(osc.fre))

    osc.only_passive()
    osc.only_space_agencies(osc.space_agencies)
    osc.only_sunsync()
    osc.no_limb()
    osc.drop_instruments()

    t0 = np.datetime64("2017-01-01")
    t1 = np.datetime64("2022-08-31")

    fre = osc.within_available(t0, t1)

    # make pivot for print statement
    instrument_cols = [
        "service",
        "satellite",
        "space_agency",
        "eol_num",
        "launch_num",
    ]
    df_freq_sel = fre.pivot(columns=instrument_cols, values="freq_num")
    df_freq_sel = df_freq_sel.sort_values(by=["service", "satellite"], axis=1)

    # print instruments
    for i, (service, satellite, space_agency, eol, launch) in enumerate(
        df_freq_sel.columns
    ):
        # find out, during which mission the satellite is available
        mission_list = []
        for mission, (mt0, mt1) in missions.items():
            if (launch < mt0) & (eol > mt1):
                mission_list.append(mission)

        print(
            "{}/{}/{}/{}-{} ({} GHz) | {}".format(
                service,
                satellite,
                space_agency,
                launch.year,
                eol.year,
                ", ".join(
                    df_freq_sel.iloc[:, i].dropna().astype("str").to_list()
                ),
                ", ".join(mission_list),
            )
        )
