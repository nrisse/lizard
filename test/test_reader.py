"""
Test the reader functions
"""

from lizard.readers.mira import read_mira
from lizard.readers.hamp import read_hamp
from lizard.readers.mirac_a import read_mirac_a, read_mirac_a_tb


class TestReader:
    def test_read_hamp_mira(self):
        """
        Test HAMP MIRA reader
        """

        ds = read_mira(flight_id="HALO-AC3_HALO_RF02")

        assert ds is not None

    def test_read_hamp(self):
        """
        Test HAMP Tb reader
        """

        ds = read_hamp(flight_id="HALO-AC3_HALO_RF02")

        assert ds is not None

    def test_read_mirac_a(self):
        """
        Test MIRAC-A reader
        """

        ds = read_mirac_a(flight_id="ACLOUD_P5_RF23")

        assert ds is not None

    def test_read_mirac_a_tb(self):
        """
        Test MIRAC-A reader
        """

        ds = read_mirac_a_tb(flight_id="ACLOUD_P5_RF23")

        assert ds is not None
