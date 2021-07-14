
from datetime import datetime
from geoengine.types import QueryRectangle
import unittest
import geoengine as ge
import requests_mock
import numpy as np


class WcsTests(unittest.TestCase):

    def setUp(self) -> None:
        ge.reset()

    def test_ndvi(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            m.post('http://mock-instance/workflow',
                   json={
                       "id": "8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62"
                   },
                   request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            m.get('http://mock-instance/wcs/8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62?service=WCS&version=1.1.1&request=GetCoverage&format=image%2Ftiff&identifier=8df9b0e6-e4b4-586e-90a3-6cf0f08c4e62&boundingbox=-90.0%2C-180.0%2C90.0%2C180.0%2Curn%3Aogc%3Adef%3Acrs%3AEPSG%3A%3A4326&time=2014-04-01T12%3A00%3A00.000%2B00%3A00&gridbasecrs=urn%3Aogc%3Adef%3Acrs%3AEPSG%3A%3A4326&gridcs=urn%3Aogc%3Adef%3Acs%3AOGC%3A0.0%3AGrid2dSquareCS&gridtype=urn%3Aogc%3Adef%3Amethod%3AWCS%3A1.1%3A2dSimpleGrid&gridorigin=90.0%2C-180.0&gridoffsets=-22.5%2C45.0',
                  body=open("tests/responses/ndvi.tiff", "rb"))

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

            workflow = ge.register_workflow(workflow_definition)

            time = datetime.strptime(
                '2014-04-01T12:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z")

            query = QueryRectangle(
                [-180.0, -90.0, 180.0, 90.0],
                [time, time],
                resolution=[360./8, 180./8],
            )

            array = workflow.get_array(query)

            self.assertEqual(array.shape, (8, 8))

            expected = np.array([
                [255, 255,  21,  11, 255, 255, 255, 255],
                [255, 100,  30, 255, 156,  94, 106,  37],
                [255,  64, 255, 255, 255,  31, 207, 255],
                [255, 255, 255, 255, 89,  255, 255, 255],
                [255, 255, 243, 255, 186, 255, 255, 255],
                [255, 255, 115, 255, 139, 255, 255, 255],
                [255, 255, 255, 255, 255, 255, 255, 255],
                [255, 255, 255, 255, 255, 255, 255, 255]])

            self.assertTrue(np.array_equal(array, expected))


if __name__ == '__main__':
    unittest.main()
