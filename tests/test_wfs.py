from datetime import datetime

from numpy import nan
from geoengine.types import QueryRectangle
import unittest
import geoengine as ge
import requests_mock
import geopandas as gpd
from shapely.geometry import Point
import geopandas.testing
import textwrap


class WfsTests(unittest.TestCase):

    def setUp(self) -> None:
        ge.reset()

    def test_geopandas(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "e327d9c3-a4f3-4bd7-a5e1-30b26cae8064",
                "user": {
                    "id": "328ca8d1-15d7-4f59-a989-5d5d72c98744",
                },
                "created": "2021-06-08T15:22:22.605891994Z",
                "validUntil": "2021-06-08T16:22:22.605892183Z",
                "project": None,
                "view": None
            })

            m.post('http://mock-instance/workflow',
                   json={
                       "id": "956d3656-2d14-5951-96a0-f962b92371cd"
                   },
                   request_headers={'Authorization': 'Bearer e327d9c3-a4f3-4bd7-a5e1-30b26cae8064'})

            m.get('http://mock-instance/wfs',
                  json={
                      "type": "FeatureCollection",
                      "features": [
                          {
                              "type": "Feature",
                              "geometry": {
                                  "type": "Point",
                                  "coordinates": [
                                      0.007420495,
                                      5.631944444
                                  ]
                              },
                              "properties": {
                                  "scalerank": 7,
                                  "website": "www.ghanaports.gov.gh",
                                  "NDVI": None,
                                  "natlscale": 10.0,
                                  "featurecla": "Port",
                                  "name": "Tema"
                              },
                              "when": {
                                  "start": "2014-04-01T00:00:00+00:00",
                                  "end": "2014-05-01T00:00:00+00:00",
                                  "type": "Interval"
                              }
                          },
                          {
                              "type": "Feature",
                              "geometry": {
                                  "type": "Point",
                                  "coordinates": [
                                      -10.05265018,
                                      5.858055556
                                  ]
                              },
                              "properties": {
                                  "scalerank": 7,
                                  "website": "www.nationalportauthorityliberia.org",
                                  "NDVI": 178,
                                  "natlscale": 10.0,
                                  "featurecla": "Port",
                                  "name": "Buchanan"
                              },
                              "when": {
                                  "start": "2014-04-01T00:00:00+00:00",
                                  "end": "2014-05-01T00:00:00+00:00",
                                  "type": "Interval"
                              }
                          },
                          {
                              "type": "Feature",
                              "geometry": {
                                  "type": "Point",
                                  "coordinates": [
                                      -57.00176678,
                                      5.951666667
                                  ]
                              },
                              "properties": {
                                  "scalerank": 6,
                                  "website": None,
                                  "NDVI": 108,
                                  "natlscale": 20.0,
                                  "featurecla": "Port",
                                  "name": "Nieuw Nickerie"
                              },
                              "when": {
                                  "start": "2014-04-01T00:00:00+00:00",
                                  "end": "2014-05-01T00:00:00+00:00",
                                  "type": "Interval"
                              }
                          },
                          {
                              "type": "Feature",
                              "geometry": {
                                  "type": "Point",
                                  "coordinates": [
                                      -3.966666667,
                                      5.233055556
                                  ]
                              },
                              "properties": {
                                  "scalerank": 5,
                                  "website": "www.paa-ci.org",
                                  "NDVI": 99,
                                  "natlscale": 30.0,
                                  "featurecla": "Port",
                                  "name": "Abidjan"
                              },
                              "when": {
                                  "start": "2014-04-01T00:00:00+00:00",
                                  "end": "2014-05-01T00:00:00+00:00",
                                  "type": "Interval"
                              }
                          },
                          {
                              "type": "Feature",
                              "geometry": {
                                  "type": "Point",
                                  "coordinates": [
                                      -52.62426384,
                                      5.158888889
                                  ]
                              },
                              "properties": {
                                  "scalerank": 5,
                                  "website": None,
                                  "NDVI": 159,
                                  "natlscale": 30.0,
                                  "featurecla": "Port",
                                  "name": "Kourou"
                              },
                              "when": {
                                  "start": "2014-04-01T00:00:00+00:00",
                                  "end": "2014-05-01T00:00:00+00:00",
                                  "type": "Interval"
                              }
                          },
                          {
                              "type": "Feature",
                              "geometry": {
                                  "type": "Point",
                                  "coordinates": [
                                      -55.13898704,
                                      5.82
                                  ]
                              },
                              "properties": {
                                  "scalerank": 5,
                                  "website": None,
                                  "NDVI": 128,
                                  "natlscale": 30.0,
                                  "featurecla": "Port",
                                  "name": "Paramaribo"
                              },
                              "when": {
                                  "start": "2014-04-01T00:00:00+00:00",
                                  "end": "2014-05-01T00:00:00+00:00",
                                  "type": "Interval"
                              }
                          },
                          {
                              "type": "Feature",
                              "geometry": {
                                  "type": "Point",
                                  "coordinates": [
                                      -4.021260306,
                                      5.283333333
                                  ]
                              },
                              "properties": {
                                  "scalerank": 3,
                                  "website": "www.paa-ci.org",
                                  "NDVI": 126,
                                  "natlscale": 75.0,
                                  "featurecla": "Port",
                                  "name": "Abidjan"
                              },
                              "when": {
                                  "start": "2014-04-01T00:00:00+00:00",
                                  "end": "2014-05-01T00:00:00+00:00",
                                  "type": "Interval"
                              }
                          }
                      ]
                  },
                  request_headers={'Authorization': 'Bearer e327d9c3-a4f3-4bd7-a5e1-30b26cae8064'})

            ge.initialize("http://mock-instance")

            workflow_definition = {
                "type": "Vector",
                "operator": {
                    "type": "RasterVectorJoin",
                    "params": {
                            "names": ["NDVI"],
                            "aggregation": "none"
                    },
                    "sources": {
                        "vector": {
                            "type": "OgrSource",
                            "params": {
                                "dataset": {
                                    "type": "internal",
                                    "datasetId": "a9623a5b-b6c5-404b-bc5a-313ff72e4e75"
                                },
                                "attributeProjection": None
                            }
                        },
                        "rasters": [{
                            "type": "GdalSource",
                            "params": {
                                "dataset": {
                                    "type": "internal",
                                    "datasetId": "36574dc3-560a-4b09-9d22-d5945f2b8093"
                                }
                            }
                        }]
                    },
                }
            }

            time = datetime.strptime(
                '2014-04-01T12:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z")

            workflow = ge.register_workflow(workflow_definition)

            df = workflow.get_dataframe(
                QueryRectangle(
                    [-60.0, 5.0, 61.0, 6.0],
                    [time, time]
                )
            )

            self.assertEqual(len(m.request_history), 3)

            workflow_request = m.request_history[1]
            self.assertEqual(workflow_request.method, "POST")
            self.assertEqual(workflow_request.url,
                             "http://mock-instance/workflow")
            self.assertEqual(workflow_request.json(), workflow_definition)

            wfs_request = m.request_history[2]
            self.assertEqual(wfs_request.method, "GET")
            self.assertEqual(wfs_request.url,
                             "http://mock-instance/wfs?service=WFS&version=2.0.0&request=GetFeature&outputFormat=application%2Fjson&typeNames=registry%3A956d3656-2d14-5951-96a0-f962b92371cd&bbox=-60.0%2C5.0%2C61.0%2C6.0&time=2014-04-01T12%3A00%3A00.000%2B00%3A00&srsName=EPSG%3A4326&queryResolution=0.1%2C0.1")

            expected_df = gpd.GeoDataFrame(
                {
                    "scalerank": [7, 7, 6, 5, 5, 5, 3],
                    "website": ["www.ghanaports.gov.gh", "www.nationalportauthorityliberia.org", None, "www.paa-ci.org", None, None, "www.paa-ci.org"],
                    "NDVI": [nan, 178.0, 108.0, 99.0, 159.0, 128.0, 126.0],
                    "natlscale": [10.0, 10.0, 20.0, 30.0, 30.0, 30.0, 75.0],
                    "featurecla": ["Port", "Port", "Port", "Port", "Port", "Port", "Port"],
                    "name": ["Tema", "Buchanan", "Nieuw Nickerie", "Abidjan", "Kourou", "Paramaribo", "Abidjan"],
                    "geometry": [
                        Point(0.007420495, 5.631944444),
                        Point(-10.05265018, 5.858055556),
                        Point(-57.00176678, 5.951666667),
                        Point(-3.966666667, 5.233055556),
                        Point(-52.62426384, 5.158888889),
                        Point(-55.13898704, 5.82),
                        Point(-4.021260306, 5.283333333),
                    ],
                    "start": [datetime.strptime(
                        '2014-04-01T00:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z") for _ in range(7)],
                    "end": [datetime.strptime(
                        '2014-05-01T00:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z") for _ in range(7)],
                },
                geometry="geometry",
                crs="EPSG:4326",
            )

            gpd.testing.assert_geodataframe_equal(df, expected_df)

    def test_repr(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "e327d9c3-a4f3-4bd7-a5e1-30b26cae8064",
                "user": {
                    "id": "328ca8d1-15d7-4f59-a989-5d5d72c98744",
                },
                "created": "2021-06-08T15:22:22.605891994Z",
                "validUntil": "2021-06-08T16:22:22.605892183Z",
                "project": None,
                "view": None
            })

            ge.initialize("http://mock-instance")

            workflow = ge.workflow_by_id("foobar")

            self.assertEqual(repr(workflow), "foobar")

    def test_result_descriptor(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "e327d9c3-a4f3-4bd7-a5e1-30b26cae8064",
                "user": {
                    "id": "328ca8d1-15d7-4f59-a989-5d5d72c98744",
                },
                "created": "2021-06-08T15:22:22.605891994Z",
                "validUntil": "2021-06-08T16:22:22.605892183Z",
                "project": None,
                "view": None
            })

            m.get('http://mock-instance/workflow/4cdf1ffe-cb67-5de2-a1f3-3357ae0112bd/metadata',
                  json={
                      "type": "vector",
                      'dataType': 'MultiPoint',
                      'spatialReference': 'EPSG:4326',
                      'columns': {
                          'scalerank': 'int',
                          'NDVI': 'int',
                          'featurecla': 'text',
                          'natlscale': 'float',
                          'website': 'text',
                          'name': 'text'
                      }
                  },
                  request_headers={'Authorization': 'Bearer e327d9c3-a4f3-4bd7-a5e1-30b26cae8064'})

            m.get('http://mock-instance/workflow/foo/metadata',
                  json={
                      'error': 'NotFound',
                      'message': 'Not Found',
                  },
                  request_headers={'Authorization': 'Bearer e327d9c3-a4f3-4bd7-a5e1-30b26cae8064'})

            ge.initialize("http://mock-instance")

            workflow = ge.workflow_by_id(
                '4cdf1ffe-cb67-5de2-a1f3-3357ae0112bd')

            result_descriptor = workflow.get_result_descriptor()

            expected_repr = '''\
                Data type:         MultiPoint
                Spatial Reference: EPSG:4326
                Columns:           scalerank: int
                                   NDVI: int
                                   featurecla: text
                                   natlscale: float
                                   website: text
                                   name: text
                '''

            self.assertEqual(
                repr(result_descriptor),
                textwrap.dedent(expected_repr)
            )

            with self.assertRaises(ge.GeoEngineException) as exception:
                workflow = ge.workflow_by_id('foo')

                result_descriptor = workflow.get_result_descriptor()

            self.assertEqual(str(exception.exception),
                             'NotFound: Not Found')


if __name__ == '__main__':
    unittest.main()
