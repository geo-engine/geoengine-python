"""Tests for WMS calls"""

import unittest
from datetime import datetime
from uuid import UUID

import geoengine as ge
from geoengine.datasets import DatasetName, StoredDataset
from geoengine.resource_identifier import UploadId

from . import UrllibMocker


class WorkflowStorageTests(unittest.TestCase):
    """Test methods for storing workflows as datasets"""

    def setUp(self) -> None:
        ge.reset(False)

    def test_storing_workflow(self):
        expected_request_text = {
            "asCog": True,
            "description": "Bar",
            "displayName": "Foo",
            "query": {
                "spatialBounds": {
                    "lowerRightCoordinate": {"x": 180, "y": -90},
                    "upperLeftCoordinate": {"x": -180, "y": 90},
                },
                "timeInterval": {"end": 1396353600000, "start": 1396353600000},
            },
        }

        with UrllibMocker() as m:
            m.post(
                "http://mock-instance/anonymous",
                json={"id": "c4983c3e-9b53-47ae-bda9-382223bd5081", "project": None, "view": None},
            )

            m.post(
                "http://mock-instance/workflow",
                json={"id": "5b9508a8-bd34-5a1c-acd6-75bb832d2d38"},
                request_headers={"Authorization": "Bearer c4983c3e-9b53-47ae-bda9-382223bd5081"},
            )

            m.get(
                "http://mock-instance/workflow/5b9508a8-bd34-5a1c-acd6-75bb832d2d38/metadata",
                json={
                    "type": "raster",
                    "dataType": "U8",
                    "spatialReference": "EPSG:4326",
                    "spatialGrid": {
                        "descriptor": "source",
                        "spatialGrid": {
                            "geoTransform": {
                                "originCoordinate": {"x": 0.0, "y": 0.0},
                                "xPixelSize": 1.0,
                                "yPixelSize": -1.0,
                            },
                            "gridBounds": {
                                "topLeftIdx": {"xIdx": 0, "yIdx": 0},
                                "bottomRightIdx": {"xIdx": 10, "yIdx": 20},
                            },
                        },
                    },
                    "bands": [{"name": "band", "measurement": {"type": "unitless"}}],
                    "time": {
                        "bounds": {"start": 0, "end": 100000},
                        "dimension": None,
                    },
                },
                request_headers={"Authorization": "Bearer c4983c3e-9b53-47ae-bda9-382223bd5081"},
            )

            m.post(
                "http://mock-instance/datasetFromWorkflow/5b9508a8-bd34-5a1c-acd6-75bb832d2d38",
                expected_request_body=expected_request_text,
                json={"taskId": "9ec828ef-c3da-4016-8cc7-79e5556267fc"},
                request_headers={"Authorization": "Bearer c4983c3e-9b53-47ae-bda9-382223bd5081"},
            )

            m.get(
                "http://mock-instance/tasks/9ec828ef-c3da-4016-8cc7-79e5556267fc/status",
                json={
                    "status": "completed",
                    "info": {"dataset": "my_new_dataset", "upload": "3086f494-d5a4-4b51-a14b-3b29f8bf7bb0"},
                    "timeTotal": "00:00:00",
                    "taskType": "create-dataset",
                    "description": "Creating dataset Foo from workflow 5b9508a8-bd34-5a1c-acd6-75bb832d2d38",
                    "timeStarted": "2023-02-16T15:25:45.390Z",
                },
            )

            ge.initialize("http://mock-instance")

            workflow_definition = {"type": "Raster", "operator": {"type": "GdalSource", "params": {"data": "ndvi"}}}

            query = ge.QueryRectangle(
                ge.SpatialPartition2D(xmin=-180.0, ymax=90.0, xmax=180.0, ymin=-90.0),
                ge.TimeInterval(start=datetime(2014, 4, 1, 12, 0), end=None),
            )

            workflow = ge.register_workflow(workflow_definition)
            task = workflow.save_as_dataset(
                query,
                None,
                "Foo",
                "Bar",
            )
            task_status = task.get_status()
            stored_dataset = StoredDataset.from_response(task_status.info)

            self.assertEqual(stored_dataset.dataset_name, DatasetName("my_new_dataset"))
            self.assertEqual(stored_dataset.upload_id, UploadId(UUID("3086f494-d5a4-4b51-a14b-3b29f8bf7bb0")))
