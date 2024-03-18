"""Tests for the datasets module."""

import unittest
import geoengine as ge
from . import UrllibMocker


class DatasetsTests(unittest.TestCase):
    """Dataset test runner."""

    def setUp(self) -> None:
        """Set up the geo engine session."""
        ge.reset(False)

    def test_list_datasets(self):
        """Test `GET /datasets`."""

        with UrllibMocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            m.get(
                'http://mock-instance/datasets?filter=foo&order=NameAsc&offset=1&limit=2',
                request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'},
                json=[{
                    'id': '35383178-4b70-421f-af82-c345c81d2e13',
                    'name': 'foobar',
                    'displayName': 'Land Cover',
                    'description': 'Land Cover',
                    'tags': [],
                    'sourceOperator': 'GdalSource',
                    'resultDescriptor': {'type': 'raster',
                                         'dataType': 'U8',
                                         'spatialReference': 'EPSG:4326',
                                         'bands': [{'name': 'band',
                                                    'measurement':
                                                    {'type': 'classification',
                                                     'measurement': 'Land Cover',
                                                        'classes': {'0': 'Water Bodies',
                                                                    '1': 'Evergreen Needleleaf Forests',
                                                                    '10': 'Grasslands',
                                                                    '11': 'Permanent Wtlands',
                                                                    '12': 'Croplands',
                                                                    '13': 'Urban and Built-Up',
                                                                    '14': 'Cropland-Natural Vegetation Mosaics',
                                                                    '15': 'Snow and Ice',
                                                                    '16': 'Barren or Sparsely Vegetated',
                                                                    '2': 'Evergreen Broadleaf Forests',
                                                                    '3': 'Deciduous Needleleaf Forests',
                                                                    '4': 'Deciduous Broadleleaf Forests',
                                                                    '5': 'Mixed Forests',
                                                                    '6': 'Closed Shrublands',
                                                                    '7': 'Open Shrublands',
                                                                    '8': 'Woody Savannas',
                                                                    '9': 'Savannas'}}}],
                                         'time': None,
                                         'bbox': {'upperLeftCoordinate': {'x': -180.0, 'y': 90.0},
                                                  'lowerRightCoordinate': {'x': 180.0, 'y': -90.0}},
                                         'resolution': {'x': 0.1, 'y': 0.1}},
                    'symbology': {'type': 'raster',
                                  'opacity': 1.0,
                                  'rasterColorizer': {
                                      'type': 'singleBand',
                                      'band': 0,
                                      'bandColorizer': {
                                          'type': 'linearGradient',
                                          'breakpoints': [{'value': 0.0, 'color': [0, 0, 255, 255]},
                                                          {'value': 8.0, 'color': [0, 255, 0, 255]},
                                                          {'value': 16.0, 'color': [255, 0, 0, 255]}],
                                          'noDataColor': [0, 0, 0, 0],
                                          'overColor': [0, 0, 0, 0],
                                          'underColor': [0, 0, 0, 0]}}}}
                      ])

            ge.initialize("http://mock-instance")

            datasets = ge.list_datasets(
                offset=1,
                limit=2,
                order=ge.DatasetListOrder.NAME_ASC,
                name_filter='foo'
            )

            self.assertEqual(len(datasets), 1)

            dataset = datasets[0]

            self.assertEqual(dataset.name, 'foobar')
            self.assertEqual(dataset.display_name, 'Land Cover')
            self.assertEqual(dataset.result_descriptor.actual_instance.type, 'raster')


if __name__ == '__main__':
    unittest.main()
