"""A module that contains classes to write raster data from a Geo Engine raster workflow."""

import logging
from datetime import datetime
from typing import cast

import numpy as np
import rasterio as rio

from geoengine.raster import ge_type_to_np
from geoengine.types import RasterResultDescriptor, TimeInterval
from geoengine.workflow import QueryRectangle, Workflow

logger = logging.getLogger("geoengine")


# pylint: disable=too-many-instance-attributes
class RasterWorkflowRioWriter:
    """
    A class to write raster data from a Geo Engine raster workflow to a GDAL dataset.
    It creates a new dataset for each time interval and writes the tiles to the dataset.
    Multiple bands are supported and the bands are written to the dataset in the order of the result descriptor.
    """

    current_dataset: rio.io.DatasetWriter | None = None
    current_time: TimeInterval | None = None
    dataset_geo_transform = None
    dataset_width = None
    dataset_height = None
    dataset_data_type = np.dtype

    dataset_prefix = None
    workflow: Workflow | None = None
    bands = None
    no_data_value = 0
    time_format = "%Y-%m-%d_%H-%M-%S"

    gdal_driver = "GTiff"
    rio_kwargs = {"tiled": True, "compress": "DEFLATE", "zlevel": 6}
    tile_size = 512
    gdal_cache_max = 32000000

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        dataset_prefix,
        workflow: Workflow,
        no_data_value=0,
        data_type=None,
        rio_kwargs=None,
        gdal_cache_max=32000000,
    ):
        """Create a new RasterWorkflowGdalWriter instance."""
        self.dataset_prefix = dataset_prefix
        self.workflow = workflow
        self.no_data_value = no_data_value

        ras_res = cast(RasterResultDescriptor, self.workflow.get_result_descriptor())
        dt = ge_type_to_np(ras_res.data_type)
        self.dataset_data_type = dt if data_type is None else data_type
        self.bands = ras_res.bands
        self.gdal_cache_max = gdal_cache_max
        if rio_kwargs:
            for key, value in rio_kwargs.items():
                self.rio_kwargs[key] = value

    def close_current_dataset(self):
        """Close the current dataset"""
        if self.current_dataset:
            if self.current_time:
                logger.debug("closing dataset for %s", self.current_time.time_str)
            del self.current_dataset
            self.current_dataset = None

    # pylint: disable=too-many-locals, too-many-statements
    def create_tiling_geo_transform_width_height(self, query: QueryRectangle):
        """Create the tiling geo transform, width and height for the current query."""

        ul_x = query.spatial_bounds.xmin
        ul_y = query.spatial_bounds.ymax
        lr_x = query.spatial_bounds.xmax
        lr_y = query.spatial_bounds.ymin
        res_x = query.spatial_resolution.x_resolution
        res_y = query.spatial_resolution.y_resolution * -1  # honor the fact that the y axis is flipped

        assert res_y < 0, "The y resolution must be negative"

        assert ul_x < lr_x, "The upper left x coordinate must be smaller than the lower right x coordinate"
        assert ul_y > lr_y, "The upper left y coordinate must be greater than the lower right y coordinate"

        ul_pixel_x = ul_x / res_x  # we can assume that the global origin is 0,0
        ul_pixel_y = ul_y / res_y
        lr_pixel_x = lr_x / res_x
        lr_pixel_y = lr_y / res_y

        assert ul_pixel_x < lr_pixel_x, "The upper left pixel x must be smaller than the lower right pixel x"
        assert ul_pixel_y < lr_pixel_y, "The upper left pixel y must be smaller than the lower right pixel y"

        tiling_ul_pixel_x = (ul_pixel_x // self.tile_size) * self.tile_size
        if ul_pixel_x % self.tile_size != 0:
            tiling_ul_pixel_x = ((ul_pixel_x // self.tile_size) - 1) * self.tile_size

        tiling_ul_pixel_y = (ul_pixel_y // self.tile_size) * self.tile_size
        if ul_pixel_y % self.tile_size != 0:
            tiling_ul_pixel_y = ((ul_pixel_y // self.tile_size) - 1) * self.tile_size

        assert tiling_ul_pixel_x <= ul_pixel_x, "Tiling upper left x pixel must be smaller than upper left x coordinate"
        assert tiling_ul_pixel_y <= ul_pixel_y, "Tiling upper left y pixel must be smaller than upper left y coordinate"

        width = int(lr_pixel_x - tiling_ul_pixel_x)
        if width % self.tile_size != 0:
            width = int((width // self.tile_size + 1) * self.tile_size)
        assert width > 0, "The width must be greater than 0"

        height = int(lr_pixel_y - tiling_ul_pixel_y)
        if height % self.tile_size != 0:
            height = int((height // self.tile_size + 1) * self.tile_size)
        assert height > 0, "The height must be greater than 0"

        assert width % self.tile_size == 0, "The width must be a multiple of the tile size"
        assert height % self.tile_size == 0, "The height must be a multiple of the tile size"

        tiling_ul_x_coord = tiling_ul_pixel_x * res_x
        tiling_ul_y_coord = tiling_ul_pixel_y * res_y
        assert tiling_ul_x_coord <= ul_x, "Tiling upper left x coordinate must be smaller than upper left x coordinate"
        assert tiling_ul_y_coord >= ul_y, "Tiling upper left y coordinate must be greater than upper left y coordinate"

        geo_transform = [tiling_ul_x_coord, res_x, 0.0, tiling_ul_y_coord, 0.0, res_y]

        if self.dataset_geo_transform is None:
            self.dataset_geo_transform = geo_transform
        else:
            assert self.dataset_geo_transform == geo_transform, "Can not change the geo transform of the dataset"

        if self.dataset_width is None:
            self.dataset_width = width
        else:
            assert self.dataset_width == width, "The width of the current dataset does not match the new one"

        if self.dataset_height is None:
            self.dataset_height = height
        else:
            assert self.dataset_height == height, "The height of the current dataset does not match the new one"

    def __create_new_dataset(self, query: QueryRectangle, gdal_cache_max=32000000):
        """Create a new dataset for the current query."""
        assert self.current_time is not None, "The current time must be set"
        time_formated_start = self.current_time.start.astype(datetime).strftime(self.time_format)
        width = self.dataset_width
        height = self.dataset_height
        geo_transform = self.dataset_geo_transform
        assert geo_transform is not None
        affine_transform = rio.Affine.from_gdal(
            geo_transform[0], geo_transform[1], geo_transform[2], geo_transform[3], geo_transform[4], geo_transform[5]
        )
        logger.debug(
            f"Creating dataset {self.dataset_prefix}{time_formated_start}.tif"
            f" with width {width}, height {height}, geo_transform {geo_transform}"
            f" rio kwargs: {self.rio_kwargs}"
        )
        assert self.bands is not None, "The bands must be set"
        number_of_bands = len(self.bands)
        dataset_data_type = self.dataset_data_type
        file_path = f"{self.dataset_prefix}{time_formated_start}.tif"

        with rio.Env(CPL_DEBUG=True, GDAL_CACHEMAX=gdal_cache_max):
            rio_dataset = rio.open(
                file_path,
                "w",
                driver=self.gdal_driver,
                width=width,
                height=height,
                count=number_of_bands,
                crs=query.srs,
                transform=affine_transform,
                dtype=dataset_data_type,
                nodata=self.no_data_value,
                **self.rio_kwargs,
            )

        for i, b in enumerate(self.bands, start=1):
            b_n = b.name
            b_m = str(b.measurement)
            rio_dataset.update_tags(i, band_name=b_n, band_measurement=b_m)

        self.current_dataset = rio_dataset

    async def query_and_write(self, query: QueryRectangle, skip_empty_times=True):
        """
        Query the raster workflow and write the resulting tiles to a GDAL dataset per timeslice.

        :param query: The QueryRectangle to write to GDAL dataset(s)
        :param skip_empty_times: Skip timeslices where all pixels are empty/nodata
        """
        self.create_tiling_geo_transform_width_height(query)

        assert self.bands is not None, "The bands must be set"
        bands = list(range(0, len(self.bands)))

        assert self.workflow is not None, "The workflow must be set"
        tile_count = 0
        empty_count = 0
        ts_count = 0
        ts_empty_count = 0
        try:
            async for tile in self.workflow.raster_stream(query, bands=bands):
                tile_count += 1
                ts_count += 1
                logger.debug("next tile. #ts_count_count %d, #total %d ", ts_count, tile_count)

                if self.current_time != tile.time:
                    logger.debug("next time step: %s", tile.time.time_str)
                    ts_count = 1
                    ts_empty_count = 1
                    self.close_current_dataset()
                    self.current_time = tile.time

                if tile.is_empty() and skip_empty_times:
                    ts_empty_count += 1
                    empty_count += 1
                    logger.debug("_empty_ tile. #ts_empty %d, #total_empty %d", ts_empty_count, empty_count)
                    continue

                if self.current_dataset is None:
                    self.__create_new_dataset(query)

                assert self.current_time == tile.time, "The time of the current dataset does not match the tile"
                assert self.dataset_geo_transform is not None, "The geo transform must be set"

                tile_ul_x = int(
                    (tile.geo_transform.x_min - self.dataset_geo_transform[0]) / self.dataset_geo_transform[1]
                )
                tile_ul_y = int(
                    (tile.geo_transform.y_max - self.dataset_geo_transform[3]) / self.dataset_geo_transform[5]
                )

                band_index = tile.band + 1

                logger.debug("tile with #pixels = %d, #empty_pixels = %d", tile.num_pixels(), tile.num_no_data_pixels())
                data = tile.to_numpy_data_array(self.no_data_value)

                assert self.tile_size == tile.size_x == tile.size_y, "Tile size does not match the expected size"
                window = rio.windows.Window(tile_ul_x, tile_ul_y, tile.size_x, tile.size_y)
                assert self.current_dataset is not None, "Dataset must be open."
                self.current_dataset.write(data, window=window, indexes=band_index)

        except Exception as inner_e:
            raise RuntimeError(f"Tile at {tile.spatial_partition().as_bbox_str()} with {tile.time}") from inner_e

        finally:
            self.close_current_dataset()
