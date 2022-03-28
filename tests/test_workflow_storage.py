'''Tests for WMS calls'''

from datetime import datetime
import unittest
import json

import requests_mock

from geoengine.types import InternalDatasetId, QueryRectangle
from geoengine.datasets import UploadId
import geoengine as ge


class WorkflowStorageTests(unittest.TestCase):
    '''Test methods for storing workflows as datasets'''

    def setUp(self) -> None:
        ge.reset(False)

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
                   additional_matcher=lambda request: request.text == json.dumps({
                       "name": "Foo",
                       "description": "Bar",
                       "query": {
                           "spatialBounds": {
                               "upperLeftCoordinate": {
                                   "x": -180.0,
                                   "y": 90.0},
                               "lowerRightCoordinate": {
                                   "x": 180.0,
                                   "y": -90.0
                               }
                           },
                           "timeInterval": {
                               "start": 1396353600000,
                               "end": 1396353600000
                           },
                           "spatialResolution": {
                               "x": 1.8,
                               "y": 1.8
                           }
                       }
                   }),
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

            stored_dataset = workflow.save_as_dataset(
                QueryRectangle(
                    [-180.0, -90.0, 180.0, 90.0],
                    [time, time],
                    resolution=(1.8, 1.8)
                ),
                "Foo",
                "Bar",
            )

            self.assertEqual(stored_dataset.dataset_id, InternalDatasetId("94230f0b-4e8a-4cba-9adc-3ace837fe5d4"))
            self.assertEqual(stored_dataset.upload_id, UploadId("3086f494-d5a4-4b51-a14b-3b29f8bf7bb0"))
