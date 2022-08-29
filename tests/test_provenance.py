'''Tests for querying provenance information'''

import unittest
from uuid import UUID
import requests_mock

from geoengine.types import InternalDataId, Provenance, ProvenanceOutput
import geoengine as ge


class ProvenanceTests(unittest.TestCase):
    '''Test runner for provenance tests'''

    def setUp(self) -> None:
        ge.reset(False)

    def test_provenance_call(self):
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
                      }
                  },
                  request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            m.get(
                # pylint: disable=line-too-long
                'http://mock-instance/workflow/5b9508a8-bd34-5a1c-acd6-75bb832d2d38/provenance',
                json=[{
                      "data": {
                          "type": "internal",
                          "datasetId": "36574dc3-560a-4b09-9d22-d5945f2b8093"
                      },
                      "provenance": {
                          "citation": "Nasa Earth Observations, MODIS Vegetation Index Products",
                          "license": "https://earthdata.nasa.gov/collaborate/open-data-services-and-software/data-information-policy",
                          "uri": "https://modis.gsfc.nasa.gov/data/dataprod/mod13.php"
                      }
                      }],
                request_headers={
                    'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'}
            )

            ge.initialize("http://mock-instance")

            workflow_definition = {
                "type": "Raster",
                "operator": {
                    "type": "GdalSource",
                    "params": {
                        "data": {
                            "type": "internal",
                            "datasetId": "36574dc3-560a-4b09-9d22-d5945f2b8093"
                        }
                    }
                }
            }

            workflow = ge.register_workflow(workflow_definition)

            provenance = workflow.get_provenance()

            self.assertEqual(provenance, [
                ProvenanceOutput(
                    # pylint: disable=line-too-long
                    InternalDataId(UUID("36574dc3-560a-4b09-9d22-d5945f2b8093")),
                    Provenance(
                        "Nasa Earth Observations, MODIS Vegetation Index Products",
                        "https://earthdata.nasa.gov/collaborate/open-data-services-and-software/data-information-policy",
                        "https://modis.gsfc.nasa.gov/data/dataprod/mod13.php"
                    ))
            ])


if __name__ == '__main__':
    unittest.main()
