'''Tests regarding raster tiles'''

import unittest
from datetime import datetime
import numpy as np
import pyarrow as pa
import rasterio as rio
import geoengine as ge


class RasterTests(unittest.TestCase):
    '''Test runner regarding raster tiles'''
    test_data: ge.RasterTile2D

    def setUp(self) -> None:
        time = np.datetime64(datetime(2020, 1, 1, 0, 0, 0, 0), 'ms')
        raster_data = rio.open("tests/responses/ndvi.tiff")
        bounds = raster_data.bounds
        no_data_value = 255  # raster_data.nodata is 0 which is propably wrong)
        numpy_array = raster_data.read(1)
        numpy_masked = np.ma.masked_equal(numpy_array, no_data_value)
        array = pa.array(numpy_masked.reshape(-1))

        self.test_data = ge.RasterTile2D(
            shape=raster_data.shape,
            data=array,
            geo_transform=ge.types.GeoTransform(
                x_min=bounds[0],
                y_max=bounds[3],
                x_pixel_size=45.0,
                y_pixel_size=-22.5,
            ),
            crs="EPSG:4326",
            time=ge.TimeInterval(
                start=time
            ),
        )

    def test_shape(self) -> None:
        '''Test the shape property'''
        self.assertEqual(self.test_data.shape, (8, 8))

    def test_data_type(self) -> None:
        '''Test the data_type property'''
        self.assertEqual(self.test_data.data_type, pa.uint8())

    def test_numpy_data_type(self) -> None:
        '''Test the numpy_data_type property'''
        self.assertEqual(self.test_data.numpy_data_type, np.uint8)

    def test_has_null_values(self) -> None:
        '''Test the has_null_values property'''
        self.assertTrue(self.test_data.has_null_values)

    def test_time_start_ms(self) -> None:
        '''Test the time_start_ms property'''
        self.assertEqual(self.test_data.time_start_ms, np.datetime64(datetime(2020, 1, 1, 0, 0, 0, 0), 'ms'))

    def test_pixel_size(self) -> None:
        '''Test the pixel_size property'''
        self.assertEqual(self.test_data.pixel_size, (45.0, -22.5))

    def test_to_numpy_data_array(self) -> None:
        '''Test the to_numpy_data_array method'''
        numpy_array = self.test_data.to_numpy_data_array()
        self.assertEqual(numpy_array.shape, (8, 8))
        self.assertEqual(numpy_array.dtype, np.uint8)

    def test_to_numpy_mask_array(self) -> None:
        '''Test the to_numpy_mask_array method'''
        numpy_array = self.test_data.to_numpy_mask_array()
        self.assertIsInstance(numpy_array, np.ndarray)
        assert isinstance(numpy_array, np.ndarray)
        self.assertEqual(numpy_array.shape, (8, 8))
        self.assertEqual(numpy_array.dtype, bool)

    def test_to_numpy_masked_array(self) -> None:
        '''Test the to_numpy_masked_array method'''
        numpy_array = self.test_data.to_numpy_masked_array()
        assert isinstance(numpy_array, np.ma.MaskedArray)
        self.assertEqual(numpy_array.shape, (8, 8))
        self.assertEqual(numpy_array.dtype, np.uint8)
        self.assertEqual(numpy_array.mask.shape, (8, 8))
        self.assertEqual(numpy_array.mask.dtype, bool)

    def test_to_xarray(self) -> None:
        '''Test the to_xarray method'''
        xarray = self.test_data.to_xarray()
        self.assertEqual(xarray.shape, (8, 8))
        self.assertEqual(xarray.dtype, np.float64)
        origin_x = xarray.x.values[0]
        origin_y = xarray.y.values[0]
        self.assertEqual(origin_x, self.test_data.geo_transform.x_min + self.test_data.geo_transform.x_pixel_size / 2)
        self.assertEqual(origin_y, self.test_data.geo_transform.y_max + self.test_data.geo_transform.y_pixel_size / 2)
