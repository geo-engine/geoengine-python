from datetime import datetime
from numpy import nan
from geoengine.types import Bbox
import unittest
import geoengine as ge
import requests_mock
import pandas as pd
import geopandas


class AuthTests(unittest.TestCase):

    def setUp(self) -> None:
        ge.reset()

    def test_upload(self):

        ge.initialize("http://localhost:3030")

        df = pd.DataFrame(
            {'City': ['Buenos Aires', 'Brasilia', 'Santiago', 'Bogota', 'Caracas'],
             'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Venezuela'],
             'index': [0, 1, 2, 3, 4],
             'Latitude': [-34.58, -15.78, -33.45, 4.60, 10.48],
             'Longitude': [-58.66, -47.91, -70.66, -74.08, -66.86]})

        gdf = geopandas.GeoDataFrame(
            df, geometry=geopandas.points_from_xy(df.Longitude, df.Latitude), crs="EPSG:4326")

        ge.upload_dataframe(gdf)


if __name__ == '__main__':
    unittest.main()
