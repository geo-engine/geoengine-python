'''
A workflow representation and methods on workflows
'''
# pylint: disable=too-many-lines
# TODO: split into multiple files

from __future__ import annotations

import asyncio
import json
import urllib.parse
from io import BytesIO
from logging import debug
from os import PathLike
from typing import Any, AsyncIterator, Dict, List, Optional, Union, Type, cast, TypedDict
from uuid import UUID

import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio.io
import requests as req
import rioxarray
from PIL import Image
from owslib.util import Authentication, ResponseWrapper
from owslib.wcs import WebCoverageService
from vega import VegaLite
import websockets
import websockets.client
import xarray as xr
import pyarrow as pa

import openapi_client
from geoengine import api
from geoengine.auth import get_session
from geoengine.colorizer import Colorizer
from geoengine.error import GeoEngineException, InputException, MethodNotCalledOnPlotException, \
    MethodNotCalledOnRasterException, MethodNotCalledOnVectorException, TypeException, check_response_for_error
from geoengine import backports
from geoengine.types import GeoTransform, ProvenanceEntry, QueryRectangle, ResultDescriptor, TimeInterval
from geoengine.tasks import Task, TaskId
from geoengine.workflow_builder.operators import Operator as WorkflowBuilderOperator


# TODO: Define as recursive type when supported in mypy: https://github.com/python/mypy/issues/731
JsonType = Union[Dict[str, Any], List[Any], int, str, float, bool, Type[None]]

Axis = TypedDict('Axis', {'title': str})
Bin = TypedDict('Bin', {'binned': bool, 'step': float})
Field = TypedDict('Field', {'field': str})
DatasetIds = TypedDict('DatasetIds', {'upload': UUID, 'dataset': UUID})
Values = TypedDict('Values', {'binStart': float, 'binEnd': float, 'Frequency': int})
X = TypedDict('X', {'field': Field, 'bin': Bin, 'axis': Axis})
X2 = TypedDict('X2', {'field': Field})
Y = TypedDict('Y', {'field': Field, 'type': str})
Encoding = TypedDict('Encoding', {'x': X, 'x2': X2, 'y': Y})
VegaSpec = TypedDict('VegaSpec', {'$schema': str, 'data': List[Values], 'mark': str, 'encoding': Encoding})


class WorkflowId:
    '''
    A wrapper around a workflow UUID
    '''

    __workflow_id: UUID

    def __init__(self, workflow_id: UUID) -> None:
        self.__workflow_id = workflow_id

    @classmethod
    def from_response(cls, response: openapi_client.AddCollection200Response) -> WorkflowId:
        '''
        Create a `WorkflowId` from an http response
        '''
        return WorkflowId(UUID(response.id))

    def __str__(self) -> str:
        return str(self.__workflow_id)

    def __repr__(self) -> str:
        return str(self)


class Workflow:
    '''
    Holds a workflow id and allows querying data
    '''

    __workflow_id: WorkflowId
    __result_descriptor: ResultDescriptor

    def __init__(self, workflow_id: WorkflowId) -> None:
        self.__workflow_id = workflow_id
        self.__result_descriptor = self.__query_result_descriptor()

    def __str__(self) -> str:
        return str(self.__workflow_id)

    def __repr__(self) -> str:
        return repr(self.__workflow_id)

    def __query_result_descriptor(self, timeout: int = 60) -> ResultDescriptor:
        '''
        Query the metadata of the workflow result
        '''

        session = get_session()

        with openapi_client.ApiClient(session.configuration) as api_client:
            workflows_api = openapi_client.WorkflowsApi(api_client)
            response = workflows_api.get_workflow_metadata_handler(str(self.__workflow_id), _request_timeout=timeout)

        debug(response)

        return ResultDescriptor.from_response(response)

    def get_result_descriptor(self) -> ResultDescriptor:
        '''
        Return the metadata of the workflow result
        '''

        return self.__result_descriptor

    def workflow_definition(self, timeout: int = 60) -> openapi_client.Workflow:
        '''Return the workflow definition for this workflow'''

        session = get_session()

        with openapi_client.ApiClient(session.configuration) as api_client:
            workflows_api = openapi_client.WorkflowsApi(api_client)
            response = workflows_api.load_workflow_handler(str(self.__workflow_id), _request_timeout=timeout)

        return response

    def get_dataframe(self, bbox: QueryRectangle, timeout: int = 3600) -> gpd.GeoDataFrame:
        '''
        Query a workflow and return the WFS result as a GeoPandas `GeoDataFrame`
        '''

        if not self.__result_descriptor.is_vector_result():
            raise MethodNotCalledOnVectorException()

        session = get_session()

        with openapi_client.ApiClient(session.configuration) as api_client:
            wfs_api = openapi_client.OGCWFSApi(api_client)
            response = wfs_api.wfs_feature_handler(
                workflow=str(self.__workflow_id),
                service=openapi_client.WfsService(openapi_client.WfsService.WFS),
                request=openapi_client.GetFeatureRequest(openapi_client.GetFeatureRequest.GETFEATURE),
                type_names=str(self.__workflow_id),
                bbox=bbox.bbox_str,
                version="2.0.0",
                time=bbox.time_str,
                srs_name=bbox.srs,
                query_resolution=str(bbox.spatial_resolution),
                _request_timeout=timeout
            )

        def geo_json_with_time_to_geopandas(geo_json):
            '''
            GeoJson has no standard for time, so we parse the when field
            separately and attach it to the data frame as columns `start`
            and `end`.
            '''

            data = gpd.GeoDataFrame.from_features(geo_json)
            data = data.set_crs(bbox.srs, allow_override=True)

            start = [f['when']['start'] for f in geo_json['features']]
            end = [f['when']['end'] for f in geo_json['features']]

            # TODO: find a good way to infer BoT/EoT

            data['start'] = gpd.pd.to_datetime(start, errors='coerce')
            data['end'] = gpd.pd.to_datetime(end, errors='coerce')

            return data

        return geo_json_with_time_to_geopandas(response.to_dict())

    def wms_get_map_as_image(self, bbox: QueryRectangle, colorizer: Colorizer) -> Image:
        '''Return the result of a WMS request as a PIL Image'''

        if not self.__result_descriptor.is_raster_result():
            raise MethodNotCalledOnRasterException()

        session = get_session()

        with openapi_client.ApiClient(session.configuration) as api_client:
            wms_api = openapi_client.OGCWMSApi(api_client)
            response = wms_api.wms_map_handler(
                workflow=str(self),
                version=openapi_client.WmsVersion(openapi_client.WmsVersion.ENUM_1_DOT_3_DOT_0),
                service=openapi_client.WmsService(openapi_client.WmsService.WMS),
                request=openapi_client.GetMapRequest(openapi_client.GetMapRequest.GETMAP),
                width=int((bbox.spatial_bounds.xmax - bbox.spatial_bounds.xmin) / bbox.spatial_resolution.x_resolution),
                height=int((bbox.spatial_bounds.ymax - bbox.spatial_bounds.ymin) / bbox.spatial_resolution.y_resolution),  # pylint: disable=line-too-long
                bbox=bbox.bbox_ogc_str,
                format=openapi_client.GetMapFormat(openapi_client.GetMapFormat.IMAGE_SLASH_PNG),
                layers=str(self),
                styles='custom:' + colorizer.to_json(),
                crs=bbox.srs,
                time=bbox.time_str
            )

        return Image.open(response)

    def plot_chart(self, bbox: QueryRectangle, timeout: int = 3600) -> VegaLite:
        '''
        Query a workflow and return the plot chart result as a vega plot
        '''

        if not self.__result_descriptor.is_plot_result():
            raise MethodNotCalledOnPlotException()

        session = get_session()

        time = urllib.parse.quote(bbox.time_str)
        spatial_bounds = urllib.parse.quote(bbox.bbox_str)
        resolution = str(bbox.spatial_resolution)

        plot_url = f'{session.server_url}/plot/{self}?bbox={spatial_bounds}&crs={bbox.srs}&time={time}'\
            f'&spatialResolution={resolution}'

        response = req.get(plot_url, headers=session.auth_header, timeout=timeout)

        check_response_for_error(response)

        response_json: JsonType = response.json()
        assert isinstance(response_json, Dict)

        vega_spec: VegaSpec = json.loads(response_json['data']['vegaString'])

        return VegaLite(vega_spec)

    def __request_wcs(
        self,
        bbox: QueryRectangle,
        timeout=3600,
        file_format: str = 'image/tiff',
        force_no_data_value: Optional[float] = None
    ) -> ResponseWrapper:
        '''
        Query a workflow and return the coverage

        Parameters
        ----------
        bbox : A bounding box for the query
        timeout : HTTP request timeout in seconds
        file_format : The format of the returned raster
        force_no_data_value: If not None, use this value as no data value for the requested raster data. \
            Otherwise, use the Geo Engine will produce masked rasters.
        '''

        if not self.__result_descriptor.is_raster_result():
            raise MethodNotCalledOnRasterException()

        session = get_session()

        # TODO: properly build CRS string for bbox
        crs = f'urn:ogc:def:crs:{bbox.srs.replace(":", "::")}'

        wcs_url = f'{session.server_url}/wcs/{self.__workflow_id}'
        wcs = WebCoverageService(
            wcs_url,
            version='1.1.1',
            auth=Authentication(auth_delegate=session.requests_bearer_auth()),
        )

        [resx, resy] = bbox.resolution_ogc

        kwargs = {}

        if force_no_data_value is not None:
            kwargs["nodatavalue"] = str(float(force_no_data_value))

        return wcs.getCoverage(
            identifier=f'{self.__workflow_id}',
            bbox=bbox.bbox_ogc,
            time=[bbox.time_str],
            format=file_format,
            crs=crs,
            resx=resx,
            resy=resy,
            timeout=timeout,
            **kwargs
        )

    def __get_wcs_tiff_as_memory_file(
        self,
        bbox: QueryRectangle,
        timeout=3600,
        force_no_data_value: Optional[float] = None
    ) -> rasterio.io.MemoryFile:
        '''
        Query a workflow and return the raster result as a memory mapped GeoTiff

        Parameters
        ----------
        bbox : A bounding box for the query
        timeout : HTTP request timeout in seconds
        force_no_data_value: If not None, use this value as no data value for the requested raster data. \
            Otherwise, use the Geo Engine will produce masked rasters.
        '''

        response = self.__request_wcs(bbox, timeout, 'image/tiff', force_no_data_value).read()

        # response is checked via `raise_on_error` in `getCoverage` / `openUrl`

        memory_file = rasterio.io.MemoryFile(response)

        return memory_file

    def get_array(
        self,
        bbox: QueryRectangle,
        timeout=3600,
        force_no_data_value: Optional[float] = None
    ) -> np.ndarray:
        '''
        Query a workflow and return the raster result as a numpy array

        Parameters
        ----------
        bbox : A bounding box for the query
        timeout : HTTP request timeout in seconds
        force_no_data_value: If not None, use this value as no data value for the requested raster data. \
            Otherwise, use the Geo Engine will produce masked rasters.
        '''

        with self.__get_wcs_tiff_as_memory_file(
            bbox,
            timeout,
            force_no_data_value
        ) as memfile, memfile.open() as dataset:
            array = dataset.read(1)

            return array

    def get_xarray(
        self,
        bbox: QueryRectangle,
        timeout=3600,
        force_no_data_value: Optional[float] = None
    ) -> xr.DataArray:
        '''
        Query a workflow and return the raster result as a georeferenced xarray

        Parameters
        ----------
        bbox : A bounding box for the query
        timeout : HTTP request timeout in seconds
        force_no_data_value: If not None, use this value as no data value for the requested raster data. \
            Otherwise, use the Geo Engine will produce masked rasters.
        '''

        with self.__get_wcs_tiff_as_memory_file(
            bbox,
            timeout,
            force_no_data_value
        ) as memfile, memfile.open() as dataset:
            data_array = rioxarray.open_rasterio(dataset)

            # helping mypy with inference
            assert isinstance(data_array, xr.DataArray)

            rio: xr.DataArray = data_array.rio
            rio.update_attrs({
                'crs': rio.crs,
                'res': rio.resolution(),
                'transform': rio.transform(),
            }, inplace=True)

            # TODO: add time information to dataset
            return data_array.load()

    # pylint: disable=too-many-arguments
    def download_raster(
        self,
        bbox: QueryRectangle,
        file_path: str,
        timeout=3600,
        file_format: str = 'image/tiff',
        force_no_data_value: Optional[float] = None
    ) -> None:
        '''
        Query a workflow and save the raster result as a file on disk

        Parameters
        ----------
        bbox : A bounding box for the query
        file_path : The path to the file to save the raster to
        timeout : HTTP request timeout in seconds
        file_format : The format of the returned raster
        force_no_data_value: If not None, use this value as no data value for the requested raster data. \
            Otherwise, use the Geo Engine will produce masked rasters.
        '''

        response = self.__request_wcs(bbox, timeout, file_format, force_no_data_value)

        with open(file_path, 'wb') as file:
            file.write(response.read())

    def get_provenance(self, timeout: int = 60) -> List[ProvenanceEntry]:
        '''
        Query the provenance of the workflow
        '''

        session = get_session()

        with openapi_client.ApiClient(session.configuration) as api_client:
            workflows_api = openapi_client.WorkflowsApi(api_client)
            response = workflows_api.get_workflow_provenance_handler(str(self.__workflow_id), _request_timeout=timeout)

        return [ProvenanceEntry.from_response(item) for item in response]

    def metadata_zip(self, path: Union[PathLike, BytesIO], timeout: int = 60) -> None:
        '''
        Query workflow metadata and citations and stores it as zip file to `path`
        '''

        session = get_session()

        provenance_url = f'{session.server_url}/workflow/{self.__workflow_id}/allMetadata/zip'

        response = req.get(provenance_url, headers=session.auth_header, timeout=timeout).content

        if isinstance(path, BytesIO):
            path.write(response)
        else:
            with open(path, 'wb') as file:
                file.write(response)

    def save_as_dataset(
            self,
            query_rectangle: openapi_client.RasterQueryRectangle,
            name: Optional[str],
            display_name: str,
            description: str = '',
            timeout: int = 3600) -> Task:
        '''Init task to store the workflow result as a layer'''

        # Currently, it only works for raster results
        if not self.__result_descriptor.is_raster_result():
            raise MethodNotCalledOnRasterException()

        session = get_session()

        with openapi_client.ApiClient(session.configuration) as api_client:
            workflows_api = openapi_client.WorkflowsApi(api_client)
            response = workflows_api.dataset_from_workflow_handler(
                str(self.__workflow_id),
                openapi_client.RasterDatasetFromWorkflow(
                    name=name,
                    display_name=display_name,
                    description=description,
                    query=query_rectangle
                ),
                _request_timeout=timeout
            )

        return Task(TaskId.from_response(response))

    async def raster_stream(
            self,
            query_rectangle: QueryRectangle,
            clip_to_query_rectangle: bool = False,
            open_timeout: int = 60) -> AsyncIterator[xr.DataArray]:
        '''Stream the workflow result as series of xarrays'''

        def read_arrow_ipc(arrow_ipc: bytes) -> pa.RecordBatch:
            reader = pa.ipc.open_file(arrow_ipc)
            # We know from the backend that there is only one record batch
            record_batch = reader.get_record_batch(0)
            return record_batch

        def create_xarray(record_batch: pa.RecordBatch) -> xr.DataArray:
            metadata = record_batch.schema.metadata
            geo_transform: GeoTransform = GeoTransform.from_response(json.loads(metadata[b'geoTransform']))
            x_size = int(metadata[b'xSize'])
            y_size = int(metadata[b'ySize'])
            spatial_reference = metadata[b'spatialReference'].decode('utf-8')
            # We know from the backend that there is only one array a.k.a. one column
            arrow_array = record_batch.column(0)

            time = TimeInterval.from_response(json.loads(metadata[b'time']))

            array = xr.DataArray(
                arrow_array.to_numpy(
                    zero_copy_only=False,  # cannot zero-copy as soon as we have nodata values
                ).reshape(x_size, y_size),
                dims=["y", "x"],
                coords={
                    'x': np.arange(
                        start=geo_transform.x_min + geo_transform.x_half_pixel_size,
                        step=geo_transform.x_pixel_size,
                        stop=geo_transform.x_max(x_size),
                    ),
                    'y': np.arange(
                        start=geo_transform.y_max + geo_transform.y_half_pixel_size,
                        step=geo_transform.y_pixel_size,
                        stop=geo_transform.y_min(y_size),
                    ),
                    'time': np.datetime64(time.start, 'ms'),  # TODO: incorporate time end?
                },
            )

            array.rio.write_crs(spatial_reference, inplace=True)

            return array

        def process_bytes(tile_bytes: Optional[bytes]) -> Optional[xr.DataArray]:
            if tile_bytes is None:
                return None

            # process the received data
            record_batch = read_arrow_ipc(tile_bytes)
            tile = create_xarray(record_batch)

            return tile

        # Currently, it only works for raster results
        if not self.__result_descriptor.is_raster_result():
            raise MethodNotCalledOnRasterException()

        session = get_session()

        url = req.Request(
            'GET',
            url=f'{session.server_url}/workflow/{self.__workflow_id}/rasterStream',
            params={
                'resultType': 'arrow',
                'spatialBounds': query_rectangle.bbox_str,
                'timeInterval': query_rectangle.time_str,
                'spatialResolution': str(query_rectangle.spatial_resolution),
            },
        ).prepare().url

        if url is None:
            raise InputException('Invalid websocket url')

        async with websockets.client.connect(
            uri=self.__replace_http_with_ws(url),
            extra_headers=session.auth_header,
            open_timeout=open_timeout,
            max_size=None,
        ) as websocket:

            tile_bytes: Optional[bytes] = None

            while websocket.open:
                async def read_new_bytes() -> Optional[bytes]:
                    # already send the next request to speed up the process
                    try:
                        await websocket.send("NEXT")
                    except websockets.exceptions.ConnectionClosed:
                        # the websocket connection is already closed, we cannot read anymore
                        return None

                    try:
                        data: Union[str, bytes] = await websocket.recv()

                        if isinstance(data, str):
                            # the server sent an error message
                            raise GeoEngineException({'error': data})

                        return data
                    except websockets.exceptions.ConnectionClosedOK:
                        # the websocket connection closed gracefully, so we stop reading
                        return None

                (tile_bytes, tile) = await asyncio.gather(
                    read_new_bytes(),
                    # asyncio.to_thread(process_bytes, tile_bytes), # TODO: use this when min Python version is 3.9
                    backports.to_thread(process_bytes, tile_bytes),
                )

                if tile is not None:
                    if clip_to_query_rectangle:
                        tile = tile.rio.clip_box(*query_rectangle.spatial_bounds.as_bbox_tuple())
                        tile = cast(xr.DataArray, tile)

                    yield tile

            # process the last tile
            tile = process_bytes(tile_bytes)

            if tile is not None:
                if clip_to_query_rectangle:
                    tile = tile.rio.clip_box(*query_rectangle.spatial_bounds.as_bbox_tuple())
                    tile = cast(xr.DataArray, tile)

                yield tile

    async def raster_stream_into_xarray(
            self,
            query_rectangle: QueryRectangle,
            clip_to_query_rectangle: bool = False,
            open_timeout: int = 60) -> xr.DataArray:
        '''
        Stream the workflow result into memory and output a single xarray.

        NOTE: You can run out of memory if the query rectangle is too large.
        '''

        tile_stream = self.raster_stream(
            query_rectangle,
            clip_to_query_rectangle=clip_to_query_rectangle,
            open_timeout=open_timeout
        )

        timesteps: List[xr.DataArray] = []

        async def read_tiles(
            remainder_tile: Optional[xr.DataArray]
        ) -> tuple[List[xr.DataArray], Optional[xr.DataArray]]:
            last_timestep: Optional[np.datetime64] = None
            tiles = []

            if remainder_tile is not None:
                last_timestep = remainder_tile.time.values
                tiles.append(remainder_tile)

            async for tile in tile_stream:
                timestep: np.datetime64 = tile.time.values
                if last_timestep is None:
                    last_timestep = timestep
                elif last_timestep != timestep:
                    return tiles, tile

                tiles.append(tile)

            # this seems to be the last time step, so just return tiles
            return tiles, None

        def merge_tiles(tiles: List[xr.DataArray]) -> Optional[xr.DataArray]:
            if len(tiles) == 0:
                return None

            combined_tiles = xr.combine_by_coords(tiles)

            if isinstance(combined_tiles, xr.Dataset):
                raise TypeException('Internal error: Merging data arrays should result in a data array.')

            return combined_tiles

        (tiles, remainder_tile) = await read_tiles(None)

        while len(tiles):
            ((new_tiles, new_remainder_tile), new_timestep) = await asyncio.gather(
                read_tiles(remainder_tile),
                backports.to_thread(merge_tiles, tiles)
                # asyncio.to_thread(merge_tiles, tiles), # TODO: use this when min Python version is 3.9
            )

            tiles = new_tiles
            remainder_tile = new_remainder_tile

            if new_timestep is not None:
                timesteps.append(new_timestep)

        output: xr.DataArray = cast(
            xr.DataArray,
            # await asyncio.to_thread( # TODO: use this when min Python version is 3.9
            await backports.to_thread(
                xr.concat,
                # TODO: This is a typings error, since the method accepts also a `xr.DataArray` and returns one
                cast(List[xr.Dataset], timesteps),
                dim='time'
            )
        )

        return output

    async def vector_stream(
            self,
            query_rectangle: QueryRectangle,
            time_start_column: str = 'time_start',
            time_end_column: str = 'time_end',
            open_timeout: int = 60) -> AsyncIterator[gpd.GeoDataFrame]:
        '''Stream the workflow result as series of `GeoDataFrame`s'''

        def read_arrow_ipc(arrow_ipc: bytes) -> pa.RecordBatch:
            reader = pa.ipc.open_file(arrow_ipc)
            # We know from the backend that there is only one record batch
            record_batch = reader.get_record_batch(0)
            return record_batch

        def create_geo_data_frame(record_batch: pa.RecordBatch,
                                  time_start_column: str,
                                  time_end_column: str) -> gpd.GeoDataFrame:
            metadata = record_batch.schema.metadata
            spatial_reference = metadata[b'spatialReference'].decode('utf-8')

            data_frame = record_batch.to_pandas()

            geometry = gpd.GeoSeries.from_wkt(data_frame[api.GEOMETRY_COLUMN_NAME])
            del data_frame[api.GEOMETRY_COLUMN_NAME]  # delete the duplicated column

            geo_data_frame = gpd.GeoDataFrame(
                data_frame,
                geometry=geometry,
                crs=spatial_reference,
            )

            # split time column
            geo_data_frame[[time_start_column, time_end_column]] = geo_data_frame[api.TIME_COLUMN_NAME].tolist()
            del geo_data_frame[api.TIME_COLUMN_NAME]  # delete the duplicated column

            # parse time columns
            for time_column in [time_start_column, time_end_column]:
                geo_data_frame[time_column] = pd.to_datetime(
                    geo_data_frame[time_column],
                    utc=True,
                    unit='ms',
                    # TODO: solve time conversion problem from Geo Engine to Python for large (+/-) time instances
                    errors='coerce',
                )

            return geo_data_frame

        def process_bytes(batch_bytes: Optional[bytes]) -> Optional[gpd.GeoDataFrame]:
            if batch_bytes is None:
                return None

            # process the received data
            record_batch = read_arrow_ipc(batch_bytes)
            tile = create_geo_data_frame(
                record_batch,
                time_start_column=time_start_column,
                time_end_column=time_end_column,
            )

            return tile

        # Currently, it only works for raster results
        if not self.__result_descriptor.is_vector_result():
            raise MethodNotCalledOnVectorException()

        session = get_session()

        url = req.Request(
            'GET',
            url=f'{session.server_url}/workflow/{self.__workflow_id}/vectorStream',
            params={
                'resultType': 'arrow',
                'spatialBounds': query_rectangle.bbox_str,
                'timeInterval': query_rectangle.time_str,
                'spatialResolution': str(query_rectangle.spatial_resolution),
            },
        ).prepare().url

        if url is None:
            raise InputException('Invalid websocket url')

        async with websockets.client.connect(
            uri=self.__replace_http_with_ws(url),
            extra_headers=session.auth_header,
            open_timeout=open_timeout,
            max_size=None,  # allow arbitrary large messages, since it is capped by the server's chunk size
        ) as websocket:

            batch_bytes: Optional[bytes] = None

            while websocket.open:
                async def read_new_bytes() -> Optional[bytes]:
                    # already send the next request to speed up the process
                    try:
                        await websocket.send("NEXT")
                    except websockets.exceptions.ConnectionClosed:
                        # the websocket connection is already closed, we cannot read anymore
                        return None

                    try:
                        data: Union[str, bytes] = await websocket.recv()

                        if isinstance(data, str):
                            # the server sent an error message
                            raise GeoEngineException({'error': data})

                        return data
                    except websockets.exceptions.ConnectionClosedOK:
                        # the websocket connection closed gracefully, so we stop reading
                        return None

                (batch_bytes, batch) = await asyncio.gather(
                    read_new_bytes(),
                    # asyncio.to_thread(process_bytes, batch_bytes), # TODO: use this when min Python version is 3.9
                    backports.to_thread(process_bytes, batch_bytes),
                )

                if batch is not None:
                    yield batch

            # process the last tile
            batch = process_bytes(batch_bytes)

            if batch is not None:
                yield batch

    async def vector_stream_into_geopandas(
            self,
            query_rectangle: QueryRectangle,
            time_start_column: str = 'time_start',
            time_end_column: str = 'time_end',
            open_timeout: int = 60) -> gpd.GeoDataFrame:
        '''
        Stream the workflow result into memory and output a single geo data frame.

        NOTE: You can run out of memory if the query rectangle is too large.
        '''

        chunk_stream = self.vector_stream(
            query_rectangle,
            time_start_column=time_start_column,
            time_end_column=time_end_column,
            open_timeout=open_timeout,
        )

        data_frame: Optional[gpd.GeoDataFrame] = None
        chunk: Optional[gpd.GeoDataFrame] = None

        async def read_dataframe() -> Optional[gpd.GeoDataFrame]:
            try:
                return await chunk_stream.__anext__()
            except StopAsyncIteration:
                return None

        def merge_dataframes(
            df_a: Optional[gpd.GeoDataFrame],
            df_b: Optional[gpd.GeoDataFrame]
        ) -> Optional[gpd.GeoDataFrame]:
            if df_a is None:
                return df_b

            if df_b is None:
                return df_a

            return pd.concat([df_a, df_b], ignore_index=True)

        while True:
            (chunk, data_frame) = await asyncio.gather(
                read_dataframe(),
                backports.to_thread(merge_dataframes, data_frame, chunk),
                # TODO: use this when min Python version is 3.9
                # asyncio.to_thread(merge_dataframes, data_frame, chunk),
            )

            # we can stop when the chunk stream is exhausted
            if chunk is None:
                break

        return data_frame

    def __replace_http_with_ws(self, url: str) -> str:
        '''
        Replace the protocol in the url from `http` to `ws`.

        For the websockets library, it is necessary that the url starts with `ws://`.
        For HTTPS, we need to use `wss://` instead.
        '''

        [protocol, url_part] = url.split('://', maxsplit=1)

        ws_prefix = 'wss://' if 's' in protocol.lower() else 'ws://'

        return f'{ws_prefix}{url_part}'


def register_workflow(workflow: Union[Dict[str, Any], WorkflowBuilderOperator], timeout: int = 60) -> Workflow:
    '''
    Register a workflow in Geo Engine and receive a `WorkflowId`
    '''

    if isinstance(workflow, WorkflowBuilderOperator):
        workflow = workflow.to_workflow_dict()

    workflow_model = openapi_client.Workflow.from_dict(workflow)

    session = get_session()

    with openapi_client.ApiClient(session.configuration) as api_client:
        workflows_api = openapi_client.WorkflowsApi(api_client)
        response = workflows_api.register_workflow_handler(workflow_model, _request_timeout=timeout)

    return Workflow(WorkflowId.from_response(response))


def workflow_by_id(workflow_id: UUID) -> Workflow:
    '''
    Create a workflow object from a workflow id
    '''

    # TODO: check that workflow exists

    return Workflow(WorkflowId(workflow_id))


def get_quota(user_id: Optional[UUID] = None, timeout: int = 60) -> openapi_client.Quota:
    '''
    Gets a user's quota. Only admins can get other users' quota.
    '''

    session = get_session()

    with openapi_client.ApiClient(session.configuration) as api_client:
        user_api = openapi_client.UserApi(api_client)

        if user_id is None:
            return user_api.quota_handler(_request_timeout=timeout)

        return user_api.get_user_quota_handler(str(user_id), _request_timeout=timeout)


def update_quota(user_id: UUID, new_available_quota: int, timeout: int = 60) -> None:
    '''
    Update a user's quota. Only admins can perform this operation.
    '''

    session = get_session()

    with openapi_client.ApiClient(session.configuration) as api_client:
        user_api = openapi_client.UserApi(api_client)
        user_api.update_user_quota_handler(
            str(user_id),
            openapi_client.UpdateQuota(
                available=new_available_quota
            ),
            _request_timeout=timeout
        )
