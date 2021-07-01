
from datetime import datetime
from geoengine.workflow import Workflow, register_workflow
from geoengine.types import QueryRectangle
import unittest
import geoengine as ge
import requests_mock
import textwrap
from vega import VegaLite


class WmsTests(unittest.TestCase):

    def setUp(self) -> None:
        ge.reset()

    def test_ndvi_histogram(self):
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

            m.get('http://mock-instance/plot/5b9508a8-bd34-5a1c-acd6-75bb832d2d38?bbox=-180.0%2C-90.0%2C180.0%2C90.0&time=2014-04-01T12%3A00%3A00.000%2B00%3A00&spatialResolution=0.1,0.1',
                  json={
                      "outputFormat": "JsonVega",
                      "plotType": "Histogram",
                      "data": {
                          "vegaString": "{\"$schema\":\"https://vega.github.io/schema/vega-lite/v4.json\",\"data\":{\"values\":[{\"binStart\":0.0,\"binEnd\":12.75,\"Frequency\":2168189},{\"binStart\":12.75,\"binEnd\":25.5,\"Frequency\":290468},{\"binStart\":25.5,\"binEnd\":38.25,\"Frequency\":69186},{\"binStart\":38.25,\"binEnd\":51.0,\"Frequency\":93070},{\"binStart\":51.0,\"binEnd\":63.75,\"Frequency\":151997},{\"binStart\":63.75,\"binEnd\":76.5,\"Frequency\":90122},{\"binStart\":76.5,\"binEnd\":89.25,\"Frequency\":97621},{\"binStart\":89.25,\"binEnd\":102.0,\"Frequency\":85046},{\"binStart\":102.0,\"binEnd\":114.75,\"Frequency\":76370},{\"binStart\":114.75,\"binEnd\":127.5,\"Frequency\":67494},{\"binStart\":127.5,\"binEnd\":140.25,\"Frequency\":66335},{\"binStart\":140.25,\"binEnd\":153.0,\"Frequency\":63511},{\"binStart\":153.0,\"binEnd\":165.75,\"Frequency\":67069},{\"binStart\":165.75,\"binEnd\":178.5,\"Frequency\":64606},{\"binStart\":178.5,\"binEnd\":191.25,\"Frequency\":64618},{\"binStart\":191.25,\"binEnd\":204.0,\"Frequency\":64525},{\"binStart\":204.0,\"binEnd\":216.75,\"Frequency\":71143},{\"binStart\":216.75,\"binEnd\":229.5,\"Frequency\":50421},{\"binStart\":229.5,\"binEnd\":242.25,\"Frequency\":29428},{\"binStart\":242.25,\"binEnd\":255.0,\"Frequency\":4908781}]},\"mark\":\"bar\",\"encoding\":{\"x\":{\"field\":\"binStart\",\"bin\":{\"binned\":true,\"step\":12.75},\"axis\":{\"title\":\"\"}},\"x2\":{\"field\":\"binEnd\"},\"y\":{\"field\":\"Frequency\",\"type\":\"quantitative\"}}}",
                          "metadata": None
                      }
                  },
                  request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            ge.initialize("http://mock-instance")

            workflow_definition = {
                "type": "Plot",
                "operator": {
                    "type": "Histogram",
                    "params": {
                        "bounds": "data",
                        "buckets": 20
                    },
                    "sources": {
                        "source": {
                            "type": "GdalSource",
                            "params": {
                                "dataset": {
                                    "internal": "36574dc3-560a-4b09-9d22-d5945f2b8093"
                                }
                            }
                        }
                    }
                }
            }

            time = datetime.strptime(
                '2014-04-01T12:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z")

            workflow = ge.register_workflow(workflow_definition)

            vega_chart = workflow.plot_chart(
                QueryRectangle(
                    [-180.0, -90.0, 180.0, 90.0],
                    [time, time]
                )
            )

            self.assertEqual(type(vega_chart), VegaLite)

            # Check requests from the mocker
            self.assertEqual(len(m.request_history), 3)

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
                      "type": "plot"
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

            expected_repr = 'Plot Result'

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
