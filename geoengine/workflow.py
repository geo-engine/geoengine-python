'''
A workflow representation and methods on workflows
'''

from __future__ import annotations

import asyncio
import json
import urllib.parse
from io import BytesIO
from logging import debug
from os import PathLike
from typing import Any, AsyncIterator, Dict, List, Optional, Union, Type, cast
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
# TODO: can be imported directly from `typing` with python >= 3.8
from typing_extensions import TypedDict
from vega import VegaLite
import websockets
import websockets.client
import xarray as xr
import pyarrow as pa

from geoengine import api
from geoengine.auth import get_session
from geoengine.colorizer import Colorizer
from geoengine.error import GeoEngineException, InputException, MethodNotCalledOnPlotException, \
    MethodNotCalledOnRasterException, MethodNotCalledOnVectorException, TypeException, check_response_for_error, \
    InvalidUrlException
from geoengine import backports
from geoengine.types import GeoTransform, ProvenanceEntry, QueryRectangle, ResultDescriptor, TimeInterval
from geoengine.tasks import Task, TaskId


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
    def from_response(cls, response: api.WorkflowId) -> WorkflowId:
        '''
        Create a `WorkflowId` from an http response
        '''
        if 'id' not in response:
            raise TypeError('Response does not contain a workflow id.')
        return WorkflowId(UUID(response['id']))

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

        response = req.get(
            f'{session.server_url}/workflow/{self.__workflow_id}/metadata',
            headers=session.auth_header,
            timeout=timeout
        ).json()

        debug(response)

        return ResultDescriptor.from_response(response)

    def get_result_descriptor(self) -> ResultDescriptor:
        '''
        Return the metadata of the workflow result
        '''

        return self.__result_descriptor

    def workflow_definition(self, timeout: int = 60) -> Dict[str, Any]:
        '''Return the workflow definition for this workflow'''

        session = get_session()

        response = req.get(
            f'{session.server_url}/workflow/{self.__workflow_id}',
            headers=session.auth_header,
            timeout=timeout
        ).json()

        return response

    def __get_wfs_url(self, bbox: QueryRectangle) -> str:
        '''Build a WFS url from a workflow and a `QueryRectangle`'''

        session = get_session()

        params = {
            'service': 'WFS',
            'version': "2.0.0",
            'request': 'GetFeature',
            'outputFormat': 'application/json',
            'typeNames': f'{self.__workflow_id}',
            'bbox': bbox.bbox_str,
            'time': bbox.time_str,
            'srsName': bbox.srs,
            'queryResolution': str(bbox.spatial_resolution)
        }

        wfs_url = req.Request(
            'GET', url=f'{session.server_url}/wfs/{self.__workflow_id}', params=params).prepare().url

        debug(f'WFS URL:\n{wfs_url}')

        if not wfs_url:
            raise InvalidUrlException('Failed to build WFS URL for workflow {self.__workflow_id}.')
        return wfs_url

    def get_wfs_get_feature_curl(self, bbox: QueryRectangle) -> str:
        '''Return the WFS url for a workflow and a `QueryRectangle` as a cURL command'''

        if not self.__result_descriptor.is_vector_result():
            raise MethodNotCalledOnVectorException()

        wfs_request = req.Request(
            'GET',
            url=self.__get_wfs_url(bbox),
            headers=get_session().auth_header
        ).prepare()

        command = "curl -X {method} -H {headers} '{uri}'"
        headers_list = [f'"{k}: {v}"' for k, v in wfs_request.headers.items()]
        headers = " -H ".join(headers_list)
        return command.format(method=wfs_request.method, headers=headers, uri=wfs_request.url)

    def get_dataframe(self, bbox: QueryRectangle, timeout: int = 3600) -> gpd.GeoDataFrame:
        '''
        Query a workflow and return the WFS result as a GeoPandas `GeoDataFrame`
        '''

        if not self.__result_descriptor.is_vector_result():
            raise MethodNotCalledOnVectorException()

        session = get_session()

        wfs_url = self.__get_wfs_url(bbox)

        data_response = req.get(wfs_url, headers=session.auth_header, timeout=timeout)

        check_response_for_error(data_response)

        data = data_response.json()

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

        return geo_json_with_time_to_geopandas(data)

    def wms_get_map_as_image(self, bbox: QueryRectangle, colorizer: Colorizer) -> Image:
        '''Return the result of a WMS request as a PIL Image'''

        wms_request = self.__wms_get_map_request(bbox, colorizer)
        response = req.Session().send(wms_request)

        check_response_for_error(response)

        return Image.open(BytesIO(response.content))

    def __wms_get_map_request(self,
                              bbox: QueryRectangle,
                              colorizer: Colorizer) -> req.PreparedRequest:
        '''Return the WMS url for a workflow and a given `QueryRectangle`'''

        if not self.__result_descriptor.is_raster_result():
            raise MethodNotCalledOnRasterException()

        session = get_session()

        width = int((bbox.spatial_bounds.xmax - bbox.spatial_bounds.xmin) / bbox.spatial_resolution.x_resolution)
        height = int((bbox.spatial_bounds.ymax - bbox.spatial_bounds.ymin) / bbox.spatial_resolution.y_resolution)

        colorizer_colorizer_str = 'custom:' + colorizer.to_json()

        params = {
            'service': 'WMS',
            'version': '1.3.0',
            'request': "GetMap",
            'layers': str(self),
            'time': bbox.time_str,
            'crs': bbox.srs,
            'bbox': bbox.bbox_ogc_str,
            'width': width,
            'height': height,
            'format': 'image/png',
            'styles': colorizer_colorizer_str,
        }

        return req.Request(
            'GET',
            url=f'{session.server_url}/wms/{str(self)}',
            params=params,
            headers=session.auth_header
        ).prepare()

    def wms_get_map_curl(self, bbox: QueryRectangle, colorizer: Colorizer) -> str:
        '''Return the WMS curl command for a workflow and a given `QueryRectangle`'''

        wms_request = self.__wms_get_map_request(bbox, colorizer)

        command = "curl -X {method} -H {headers} '{uri}'"
        headers_list = [f'"{k}: {v}"' for k, v in wms_request.headers.items()]
        headers = " -H ".join(headers_list)
        return command.format(method=wms_request.method, headers=headers, uri=wms_request.url)

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

        no_data_value = ""
        if force_no_data_value is not None:
            no_data_value = str(float(force_no_data_value))

        return wcs.getCoverage(
            identifier=f'{self.__workflow_id}',
            bbox=bbox.bbox_ogc,
            time=[urllib.parse.quote_plus(bbox.time_str)],
            format=file_format,
            crs=crs,
            resx=resx,
            resy=resy,
            timeout=timeout,
            nodatavalue=no_data_value,
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

        provenance_url = f'{session.server_url}/workflow/{self.__workflow_id}/provenance'

        response = req.get(provenance_url, headers=session.auth_header, timeout=timeout).json()

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
            query_rectangle: api.RasterQueryRectangle,
            name: str,
            description: str = '',
            timeout: int = 3600) -> Task:
        '''Init task to store the workflow result as a layer'''

        # Currently, it only works for raster results
        if not self.__result_descriptor.is_raster_result():
            raise MethodNotCalledOnRasterException()

        session = get_session()

        request_body = {
            'name': name,
            'description': description,
            'query': query_rectangle,
        }

        response = req.post(
            url=f'{session.server_url}/datasetFromWorkflow/{self.__workflow_id}',
            json=request_body,
            headers=session.auth_header,
            timeout=timeout
        )

        check_response_for_error(response)

        return Task(TaskId.from_response(response.json()))

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
                    'time': time.start,  # TODO: incorporate time end?
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

        # for the websockets library, it is necessary that the url starts with `ws://``
        [_, url_part] = url.split('://', maxsplit=1)

        async with websockets.client.connect(
            uri=f'ws://{url_part}',
            extra_headers=session.auth_header,
            open_timeout=open_timeout,
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

        # for the websockets library, it is necessary that the url starts with `ws://``
        [_, url_part] = url.split('://', maxsplit=1)

        async with websockets.client.connect(
            uri=f'ws://{url_part}',
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


def register_workflow(workflow: Dict[str, Any], timeout: int = 60) -> Workflow:
    '''
    Register a workflow in Geo Engine and receive a `WorkflowId`
    '''

    session = get_session()

    workflow_response = req.post(
        f'{session.server_url}/workflow',
        json=workflow,
        headers=session.auth_header,
        timeout=timeout
    ).json()

    return Workflow(WorkflowId.from_response(workflow_response))


def workflow_by_id(workflow_id: UUID) -> Workflow:
    '''
    Create a workflow object from a workflow id
    '''

    # TODO: check that workflow exists

    return Workflow(WorkflowId(workflow_id))


def get_quota(user_id: Optional[UUID] = None, timeout: int = 60) -> api.Quota:
    '''
    Gets a user's quota. Only admins can get other users' quota.
    '''

    session = get_session()

    url = f'{session.server_url}/quota'

    if user_id is not None:
        url = f'{session.server_url}/quotas/{user_id}'

    quota_response = req.get(
        url,
        headers=session.auth_header,
        timeout=timeout
    ).json()

    return api.Quota({
        "available": quota_response["available"],
        "used": quota_response["used"]
    })


def update_quota(user_id: UUID, new_available_quota: int, timeout: int = 60) -> None:
    '''
    Update a user's quota. Only admins can perform this operation.
    '''

    session = get_session()

    req.post(
        f'{session.server_url}/quotas/{user_id}',
        headers=session.auth_header,
        json=api.UpdateQuota({
            'available': new_available_quota
        }),
        timeout=timeout
    )
