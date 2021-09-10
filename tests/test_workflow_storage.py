'''Tests for WMS calls'''

from datetime import datetime
import unittest

import requests_mock

from geoengine.types import InternalDatasetId, QueryRectangle
import geoengine as ge


class WorkflowStorageTests(unittest.TestCase):
    '''WMS test runner'''

    def setUp(self) -> None:
        ge.reset()

    def test_storing_workflow(self):
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

            m.post('http://mock-instance/datasetFromWorkflow/5b9508a8-bd34-5a1c-acd6-75bb832d2d38',
                   json={
                       "upload": "3086f494-d5a4-4b51-a14b-3b29f8bf7bb0",
                       "dataset": {
                           "type": "internal",
                           "datasetId": "94230f0b-4e8a-4cba-9adc-3ace837fe5d4"
                       }
                   },
                   request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

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

            dataset_id = workflow.save_as_layer(
                "Foo",
                "Bar",
                QueryRectangle(
                    [-180.0, -90.0, 180.0, 90.0],
                    [time, time],
                    resolution=(1.8, 1.8)
                ),
            )

            self.assertEqual(dataset_id, InternalDatasetId("94230f0b-4e8a-4cba-9adc-3ace837fe5d4"))
