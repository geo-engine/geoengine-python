
from datetime import datetime
from geoengine.workflow import Workflow, register_workflow

from geoengine.types import QueryRectangle
import unittest
import geoengine as ge
import requests_mock
import textwrap
import cartopy.mpl.geoaxes
from cartopy.tests.mpl import ImageTesting
import responses


class WmsTests(unittest.TestCase):

    def setUp(self) -> None:
        ge.reset()

    @responses.activate
    @ImageTesting(['wms'], tolerance=0)
    def test_ndvi(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            m.post('http://mock-instance/workflow',
                   json={
                       "id": "5b9508a8-bd34-5a1c-acd6-75bb832d2d38"
                   },
                   request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            # Unfortunately, we need a separate library to catch the request from the WMS call
            responses.add(
                'GET',
                'http://mock-instance/wms?service=WMS&version=1.3.0&request=GetMap&layers=5b9508a8-bd34-5a1c-acd6-75bb832d2d38&styles=&width=620&height=310&crs=EPSG:4326&bbox=-90.0,-180.0,90.0,180.0&format=image/png&transparent=FALSE&bgcolor=0xFFFFFF&exceptions=XML&time=2014-04-01T12%3A00%3A00.000%2B00%3A00',
                match_querystring=True,
                body=open("tests/responses/wms-ndvi.png",
                          "rb").read(),
                content_type='image/png'
            )

            ge.initialize("http://mock-instance")

            workflow_definition = {
                "type": "Raster",
                "operator": {
                    "type": "GdalSource",
                    "params": {
                        "dataset": {
                            "type": "internal",
                            "datasetId": "36574dc3-560a-4b09-9d22-d5945f2b8093"
                        }
                    }
                }
            }

            time = datetime.strptime(
                '2014-04-01T12:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z")

            workflow = ge.register_workflow(workflow_definition)

            ax = workflow.plot_image(
                QueryRectangle(
                    [-180.0, -90.0, 180.0, 90.0],
                    [time, time]
                )
            )

            ax.plot()

            self.assertEqual(type(ax), cartopy.mpl.geoaxes.GeoAxesSubplot)

            # Check requests from the mocker
            self.assertEqual(len(m.request_history), 2)

            workflow_request = m.request_history[1]
            self.assertEqual(workflow_request.method, "POST")
            self.assertEqual(workflow_request.url,
                             "http://mock-instance/workflow")
            self.assertEqual(workflow_request.json(), workflow_definition)

    def test_result_descriptor(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            m.get('http://mock-instance/workflow/5b9508a8-bd34-5a1c-acd6-75bb832d2d38/metadata',
                  json={
                      "type": "raster",
                      "dataType": "U8",
                      "spatialReference": "EPSG:4326",
                      "measurement": {
                          "type": "unitless"
                      },
                      "noDataValue": 0.0
                  },
                  request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            m.get('http://mock-instance/workflow/foo/metadata',
                  json={
                      'error': 'NotFound',
                      'message': 'Not Found',
                  },
                  request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            ge.initialize("http://mock-instance")

            workflow = ge.workflow_by_id(
                '5b9508a8-bd34-5a1c-acd6-75bb832d2d38')

            result_descriptor = workflow.get_result_descriptor()

            expected_repr = '''\
                Data type:         U8
                Spatial Reference: EPSG:4326
                Measurement:       {'type': 'unitless'}
                No Data Value:     0.0
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
