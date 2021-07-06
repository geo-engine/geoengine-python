from geoengine.datasets import InternalDatasetId, OgrSourceDatasetTimeType, OgrSourceDuration, OgrSourceTimeFormat, pandas_dtype_to_column_type
from geoengine.types import TimeStepGranularity
import unittest
import geoengine as ge
import requests_mock
import pandas as pd
import geopandas


class UploadTests(unittest.TestCase):

    def setUp(self) -> None:
        ge.reset()

    def test_upload(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "c4983c3e-9b53-47ae-bda9-382223bd5081",
                "project": None,
                "view": None
            })

            m.post('http://mock-instance/upload',
                   json={
                       "id": "c314ff6d-3e37-41b4-b9b2-3669f13f7369"
                   },
                   request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            m.post('http://mock-instance/dataset',
                   json={
                       'id': {
                           'type': 'internal',
                           'datasetId': 'fc5f9e0f-ac97-421f-a5be-d701915ceb6f'
                       }
                   },
                   request_headers={'Authorization': 'Bearer c4983c3e-9b53-47ae-bda9-382223bd5081'})

            ge.initialize("http://mock-instance")

            df = pd.DataFrame(
                {
                    'label': ['NA', 'DE'],
                    'index': [0, 1],
                    'rnd': [34.34, 567.547]
                })

            polygons = ['Polygon((-121.46484375 47.109375, -99.31640625 17.2265625, -56.42578125 52.03125,-121.46484375 47.109375))',
                        'Polygon((4.74609375 53.61328125, 5.09765625 43.06640625, 15.1171875 43.76953125, 15.1171875 54.4921875, 4.74609375 53.61328125))']

            gdf = geopandas.GeoDataFrame(
                df, geometry=geopandas.GeoSeries.from_wkt(polygons), crs="EPSG:4326")

            id = ge.upload_dataframe(gdf)

            self.assertEqual(id, InternalDatasetId(
                "fc5f9e0f-ac97-421f-a5be-d701915ceb6f"))

    def test_time_specification(self):
        time = OgrSourceDatasetTimeType.start(
            'start', OgrSourceTimeFormat.auto(), OgrSourceDuration.value(10, TimeStepGranularity.minutes))

        self.assertEqual(time.to_dict(), {
            'type': 'start',
            'startField': 'start',
            'startFormat': {
                'format': 'auto'
            },
            'duration': {
                'type': 'value',
                'step': 10,
                'granularity': 'Minutes'
            }
        })


if __name__ == '__main__':
    unittest.main()
