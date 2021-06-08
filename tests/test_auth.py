from datetime import datetime
from geoengine.types import Bbox
import unittest
import geoengine as ge
import requests as req
import requests_mock
import geopandas as gpd
from shapely.geometry import Point


class AuthTests(unittest.TestCase):

    def setUp(self) -> None:
        ge.reset()

    def test_uninitialized(self):
        with self.assertRaises(ge.UninitializedException) as exception:
            ge.geopandas_by_workflow_id(
                "foobar",
                Bbox(
                    [-180, -90, 180, 90],
                    [datetime.now(), datetime.now()]
                )
            )

        self.assertEqual(str(exception.exception),
                         'You have to call `initialize` before using other functionality')

    def test_initialize(self):
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

            self.assertEqual(type(ge.get_session()),
                             ge.Session)

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

            workflow = {
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
                                "dataset": {"internal": "a9623a5b-b6c5-404b-bc5a-313ff72e4e75"},
                                "attributeProjection": None
                            }
                        },
                        "rasters": [{
                            "type": "GdalSource",
                            "params": {
                                "dataset": {"internal": "36574dc3-560a-4b09-9d22-d5945f2b8093"}
                            }
                        }]
                    },
                }
            }

            time = datetime.strptime(
                '2014-04-01T12:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z")

            df = ge.geopandas_by_workflow(
                workflow,
                Bbox(
                    [-60.0, 5.0, 61.0, 6.0],
                    [time, time]
                )
            )

            self.assertEqual(len(m.request_history), 3)

            workflow_request = m.request_history[1]
            self.assertEqual(workflow_request.method, "POST")
            self.assertEqual(workflow_request.url,
                             "http://mock-instance/workflow")
            self.assertEqual(workflow_request.json(), workflow)

            wfs_request = m.request_history[2]
            self.assertEqual(wfs_request.method, "GET")
            self.assertEqual(wfs_request.url,
                             "http://mock-instance/wfs?service=WFS&version=2.0.0&request=GetFeature&outputFormat=application%2Fjson&typeNames=registry%3A956d3656-2d14-5951-96a0-f962b92371cd&bbox=-60.0%2C5.0%2C61.0%2C6.0&time=2014-04-01T12%3A00%3A00.000%2B00%3A00&srsName=EPSG%3A4326")

            print(df)
            print(df.geometry)

            print(gpd.GeoDataFrame(
                {
                    "geometry": [Point(0.00742, 5.63194)],
                },
                geometry="geometry").geometry)

            self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
