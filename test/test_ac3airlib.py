"""
Test ac3airborne library tools
"""

from lizard.ac3airlib import get_all_flights


def test_get_all_flights():
    assert (
        len(
            get_all_flights(
                ["ACLOUD", "AFLUX", "MOSAiC-ACA", "HALO-AC3"], "P5"
            )
        )
        == 56
    )
