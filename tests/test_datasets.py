"""Tests for the datasets module."""

import unittest
import geoengine as ge
from tests.ge_test import GeoEngineTestInstance


class DatasetsTests(unittest.TestCase):
    """Dataset test runner."""

    def setUp(self) -> None:
        """Set up the geo engine session."""
        ge.reset(False)

    def test_list_datasets(self):
        """Test `GET /datasets`."""

        # TODO: use `enterContext(cm)` instead of `with cm:` in Python 3.11
        with GeoEngineTestInstance() as ge_instance:
            ge_instance.wait_for_ready()

            ge.initialize(ge_instance.address())

            datasets = ge.list_datasets(
                offset=0,
                limit=10,
                order=ge.DatasetListOrder.NAME_ASC,
                name_filter="Natural Earth II"
            )

            self.assertEqual(len(datasets), 3)

            dataset = datasets[0]

            self.assertEqual(dataset.name, 'ne2_raster_blue')
            self.assertEqual(dataset.display_name, 'Natural Earth II – Blue')
            self.assertEqual(dataset.result_descriptor.actual_instance.type, 'raster')


if __name__ == '__main__':
    unittest.main()
