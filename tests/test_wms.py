from datetime import datetime
from geoengine.workflow import Workflow, register_workflow

from numpy import nan
from geoengine.types import Bbox
import unittest
import geoengine as ge
import requests_mock
import geopandas as gpd
import geopandas.testing
from shapely.geometry import Point
import textwrap
import os


class WmsTests(unittest.TestCase):

    def setUp(self) -> None:
        ge.reset()

    def test_ndvi(self):
        with open(os.devnull) as m:  # requests_mock.Mocker() as m:
            # m.post('http://mock-instance/anonymous', json={
            #     "id": "e327d9c3-a4f3-4bd7-a5e1-30b26cae8064",
            #     "user": {
            #         "id": "328ca8d1-15d7-4f59-a989-5d5d72c98744",
            #     },
            #     "created": "2021-06-08T15:22:22.605891994Z",
            #     "validUntil": "2021-06-08T16:22:22.605892183Z",
            #     "project": None,
            #     "view": None
            # })

            # m.post('http://mock-instance/workflow',
            #        json={
            #            "id": "956d3656-2d14-5951-96a0-f962b92371cd"
            #        },
            #        request_headers={'Authorization': 'Bearer e327d9c3-a4f3-4bd7-a5e1-30b26cae8064'})

            ge.initialize("http://peter.geoengine.io:6060")

            workflow_definition = {
                "type": "Raster",
                "operator": {
                    "type": "GdalSource",
                    "params": {
                        "dataset": {"internal": "36574dc3-560a-4b09-9d22-d5945f2b8093"}
                    }
                }
            }

            time = datetime.strptime(
                '2014-04-01T12:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z")

            workflow = ge.register_workflow(workflow_definition)

            m = workflow.get_image(
                Bbox(
                    [-180.0, -90.0, 180.0, 90.0],
                    [time, time]
                )
            )

            print(m)

            # self.assertEqual(len(m.request_history), 3)

            # workflow_request = m.request_history[1]
            # self.assertEqual(workflow_request.method, "POST")
            # self.assertEqual(workflow_request.url,
            #                  "http://mock-instance/workflow")
            # self.assertEqual(workflow_request.json(), workflow_definition)

            # wfs_request = m.request_history[2]
            # self.assertEqual(wfs_request.method, "GET")
            # self.assertEqual(wfs_request.url,
            #                  "http://mock-instance/wfs?service=WFS&version=2.0.0&request=GetFeature&outputFormat=application%2Fjson&typeNames=registry%3A956d3656-2d14-5951-96a0-f962b92371cd&bbox=-60.0%2C5.0%2C61.0%2C6.0&time=2014-04-01T12%3A00%3A00.000%2B00%3A00&srsName=EPSG%3A4326&queryResolution=0.1")

            # expected_df = gpd.GeoDataFrame(
            #     {
            #         "scalerank": [7, 7, 6, 5, 5, 5, 3],
            #         "website": ["www.ghanaports.gov.gh", "www.nationalportauthorityliberia.org", None, "www.paa-ci.org", None, None, "www.paa-ci.org"],
            #         "NDVI": [nan, 178.0, 108.0, 99.0, 159.0, 128.0, 126.0],
            #         "natlscale": [10.0, 10.0, 20.0, 30.0, 30.0, 30.0, 75.0],
            #         "featurecla": ["Port", "Port", "Port", "Port", "Port", "Port", "Port"],
            #         "name": ["Tema", "Buchanan", "Nieuw Nickerie", "Abidjan", "Kourou", "Paramaribo", "Abidjan"],
            #         "geometry": [
            #             Point(0.007420495, 5.631944444),
            #             Point(-10.05265018, 5.858055556),
            #             Point(-57.00176678, 5.951666667),
            #             Point(-3.966666667, 5.233055556),
            #             Point(-52.62426384, 5.158888889),
            #             Point(-55.13898704, 5.82),
            #             Point(-4.021260306, 5.283333333),
            #         ],
            #         "start": [datetime.strptime(
            #             '2014-04-01T00:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z") for _ in range(7)],
            #         "end": [datetime.strptime(
            #             '2014-05-01T00:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z") for _ in range(7)],
            #     },
            #     geometry="geometry",
            #     crs="EPSG:4326",
            # )

            # gpd.testing.assert_geodataframe_equal(df, expected_df)

    def test_result_descriptor(self):
        with open(os.devnull) as m:  # requests_mock.Mocker() as m:
            # m.post('http://mock-instance/anonymous', json={
            #     "id": "e327d9c3-a4f3-4bd7-a5e1-30b26cae8064",
            #     "user": {
            #         "id": "328ca8d1-15d7-4f59-a989-5d5d72c98744",
            #     },
            #     "created": "2021-06-08T15:22:22.605891994Z",
            #     "validUntil": "2021-06-08T16:22:22.605892183Z",
            #     "project": None,
            #     "view": None
            # })

            # m.get('http://mock-instance/workflow/4cdf1ffe-cb67-5de2-a1f3-3357ae0112bd/metadata',
            #       json={
            #           'dataType': 'MultiPoint',
            #           'spatialReference': 'EPSG:4326',
            #           'columns': {
            #               'scalerank': 'int',
            #               'NDVI': 'int',
            #               'featurecla': 'text',
            #               'natlscale': 'float',
            #               'website': 'text',
            #               'name': 'text'
            #           }
            #       },
            #       request_headers={'Authorization': 'Bearer e327d9c3-a4f3-4bd7-a5e1-30b26cae8064'})

            # m.get('http://mock-instance/workflow/foo/metadata',
            #       json={
            #           'error': 'NotFound',
            #           'message': 'Not Found',
            #       },
            #       request_headers={'Authorization': 'Bearer e327d9c3-a4f3-4bd7-a5e1-30b26cae8064'})

            # ge.initialize("http://mock-instance")
            ge.initialize("http://peter.geoengine.io:6060")

            # workflow = ge.workflow_by_id(
            #    '36574dc3-560a-4b09-9d22-d5945f2b8093')

            workflow = ge.register_workflow({
                "type": "Raster",
                "operator": {
                    "type": "GdalSource",
                    "params": {
                        "dataset": {"internal": "36574dc3-560a-4b09-9d22-d5945f2b8093"}
                    }
                }
            })

            result_descriptor = workflow.get_result_descriptor()

            expected_repr = '''\
                Data type:         U8
                Spatial Reference: EPSG:4326
                Measurement:       unitless
                No Data Value:     None
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
