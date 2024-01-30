'''Raster data types'''
from __future__ import annotations
import json
from typing import Optional, Tuple, Union, cast
import numpy as np
import pyarrow as pa
import xarray as xr
import geoengine_openapi_client
import geoengine.types as gety


# pylint: disable=R0902
class RasterTile2D:
    '''A 2D raster tile as produced by the Geo Engine'''
    size_x: int
    size_y: int
    data: pa.Array
    geo_transform: gety.GeoTransform
    crs: str
    time: gety.TimeInterval
    band: int
    tile_idx: Tuple[int, int]

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            shape: Tuple[int, int],
            data: pa.Array,
            geo_transform: gety.GeoTransform,
            crs: str,
            time: gety.TimeInterval,
            band: int,
            tile_idx: Tuple[int, int]
    ):
        '''Create a RasterTile2D object'''
        self.size_y, self.size_x = shape
        self.data = data
        self.geo_transform = geo_transform
        self.crs = crs
        self.time = time
        self.band = band
        self.tile_idx = tile_idx

    @property
    def shape(self) -> Tuple[int, int]:
        '''Return the shape of the raster tile in numpy order (y_size, x_size)'''
        return (self.size_y, self.size_x)

    @property
    def data_type(self) -> pa.DataType:
        '''Return the arrow data type of the raster tile'''
        return self.data.type

    @property
    def numpy_data_type(self) -> np.dtype:
        '''Return the numpy dtype of the raster tile'''
        return self.data_type.to_pandas_dtype()

    @property
    def has_null_values(self) -> bool:
        '''Return whether the raster tile has null values'''
        return self.data.null_count > 0

    @property
    def time_start_ms(self) -> np.datetime64:
        return np.datetime64(self.time.start, 'ms')

    @property
    def time_end_ms(self) -> np.datetime64:
        return np.datetime64(self.time.end, 'ms')

    @property
    def pixel_size(self) -> Tuple[float, float]:
        return (self.geo_transform.x_pixel_size, self.geo_transform.y_pixel_size)

    def to_numpy_data_array(self, fill_null_value=0) -> np.ndarray:
        '''
        Return the raster tile as a numpy array.
        Caution: this will not mask nodata values but replace them with the provided value !
        '''
        nulled_array = self.data.fill_null(fill_null_value)
        return nulled_array.to_numpy(
            zero_copy_only=True,  # data was already copied when creating the "null filled" array
        ).reshape(self.shape)

    def to_numpy_mask_array(self, nan_is_null=False) -> Optional[np.ndarray]:
        '''
        Return the raster tiles mask as a numpy array.
        True means no data, False means data.
        If the raster tile has no null values, None is returned.
        It is possible to specify whether NaN values should be considered as no data when creating the mask.
        '''
        numpy_mask = None
        if self.has_null_values:
            numpy_mask = self.data.is_null(
                nan_is_null=nan_is_null  # nan is not no data
            ).to_numpy(
                zero_copy_only=False  # cannot zero-copy with bools
            ).reshape(self.shape)
        return numpy_mask

    def to_numpy_masked_array(self, nan_is_null=False) -> np.ma.MaskedArray:
        '''Return the raster tile as a masked numpy array'''
        numpy_data = self.to_numpy_data_array()
        maybe_numpy_mask = self.to_numpy_mask_array(nan_is_null=nan_is_null)

        assert maybe_numpy_mask is None or maybe_numpy_mask.shape == numpy_data.shape

        numpy_mask: Union[np.ndarray, np.ma.MaskType] = np.ma.nomask if maybe_numpy_mask is None else maybe_numpy_mask

        numpy_masked_data: np.ma.MaskedArray = np.ma.masked_array(numpy_data, mask=numpy_mask)

        return numpy_masked_data

    def coords_x(self, pixel_center=False) -> np.ndarray:
        '''
        Return the x coordinates of the raster tile
        If pixel_center is True, the coordinates will be the center of the pixels.
        Otherwise they will be the upper left edges.
        '''
        start = self.geo_transform.x_min

        if pixel_center:
            start += self.geo_transform.x_half_pixel_size

        return np.arange(
            start=start,
            stop=self.geo_transform.x_max(self.size_x),
            step=self.geo_transform.x_pixel_size,
        )

    def coords_y(self, pixel_center=False) -> np.ndarray:
        '''
        Return the y coordinates of the raster tile
        If pixel_center is True, the coordinates will be the center of the pixels.
        Otherwise they will be the upper left edges.
        '''
        start = self.geo_transform.y_max

        if pixel_center:
            start += self.geo_transform.y_half_pixel_size

        return np.arange(
            start=start,
            stop=self.geo_transform.y_min(self.size_y),
            step=self.geo_transform.y_pixel_size,
        )

    def to_xarray(self, clip_with_bounds: Optional[gety.SpatialBounds] = None) -> xr.DataArray:
        '''
        Return the raster tile as an xarray.DataArray.
        Xarray does not support masked arrays.
        Masked pixels are converted to NaNs and the nodata value is set to NaN as well.
        '''
        array = xr.DataArray(
            self.to_numpy_masked_array(),
            dims=["y", "x"],
            coords={
                'x': self.coords_x(pixel_center=True),
                'y': self.coords_y(pixel_center=True),
                'time': self.time_start_ms,  # TODO: incorporate time end?
                'band': self.band,
            }
        )
        array.rio.write_crs(self.crs, inplace=True)

        array.attrs['tile_idx_y'] = self.tile_idx[0]
        array.attrs['tile_idx_x'] = self.tile_idx[1]

        if clip_with_bounds is not None:
            array = array.rio.clip_box(*clip_with_bounds.as_bbox_tuple())
            array = cast(xr.DataArray, array)

        return array

    def spatial_partition(self) -> gety.SpatialPartition2D:
        '''Return the spatial partition of the raster tile'''
        return gety.SpatialPartition2D(
            self.geo_transform.x_min,
            self.geo_transform.y_min(self.size_y),
            self.geo_transform.x_max(self.size_x),
            self.geo_transform.y_max,
        )

    def spatial_resolution(self) -> gety.SpatialResolution:
        return self.geo_transform.spatial_resolution()

    @staticmethod
    def from_ge_record_batch(record_batch: pa.RecordBatch) -> RasterTile2D:
        '''Create a RasterTile2D from an Arrow record batch recieved from the Geo Engine'''
        metadata = record_batch.schema.metadata
        geo_transform = gety.GeoTransform.from_response(
            geoengine_openapi_client.GdalDatasetGeoTransform.from_json(metadata[b'geoTransform'])
        )
        x_size = int(metadata[b'xSize'])
        y_size = int(metadata[b'ySize'])
        spatial_reference = metadata[b'spatialReference'].decode('utf-8')
        # We know from the backend that there is only one array a.k.a. one column
        arrow_array = record_batch.column(0)

        time = gety.TimeInterval.from_response(json.loads(metadata[b'time']))

        band = int(metadata[b'band'])

        tile_idx_split = metadata[b'tileIdx'].decode('utf-8').split(',')
        if len(tile_idx_split) != 2:
            raise ValueError(f"Expected tile_idx to have exactly 2 elements, but got {len(tile_idx_split)}")
        tile_idx = (int(tile_idx_split[0]), int(tile_idx_split[1]))

        return RasterTile2D(
            (y_size, x_size),
            arrow_array,
            geo_transform,
            spatial_reference,
            time,
            band,
            tile_idx
        )
