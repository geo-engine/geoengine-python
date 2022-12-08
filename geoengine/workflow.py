'''
A workflow representation and methods on workflows
'''

from __future__ import annotations

import json
import urllib.parse
from io import BytesIO
from logging import debug
from os import PathLike
from typing import Any, Dict, List, Optional, Union, Type
from uuid import UUID

import geopandas as gpd
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
from xarray import DataArray

from geoengine.auth import get_session
from geoengine.colorizer import Colorizer
from geoengine.error import GeoEngineException, MethodNotCalledOnPlotException, MethodNotCalledOnRasterException, \
    MethodNotCalledOnVectorException, SpatialReferenceMismatchException, check_response_for_error
from geoengine.tasks import Task, TaskId
from geoengine.types import ProvenanceOutput, QueryRectangle, ResultDescriptor

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
    def from_response(cls, response: Dict[str, str]) -> WorkflowId:
        '''
        Create a `WorkflowId` from an http response
        '''
        if 'id' not in response:
            raise GeoEngineException(response)

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

        params = dict(
            service='WFS',
            version="2.0.0",
            request='GetFeature',
            outputFormat='application/json',
            typeNames=f'{self.__workflow_id}',
            bbox=bbox.bbox_str,
            time=bbox.time_str,
            srsName=bbox.srs,
            queryResolution=f'{bbox.resolution[0]},{bbox.resolution[1]}'
        )

        wfs_url = req.Request(
            'GET', url=f'{session.server_url}/wfs/{self.__workflow_id}', params=params).prepare().url

        debug(f'WFS URL:\n{wfs_url}')

        if not wfs_url:
            raise Exception('Failed to build WFS URL for workflow {self.__workflow_id}.')
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

        width = int((bbox.xmax - bbox.xmin) / bbox.resolution[0])
        height = int((bbox.ymax - bbox.ymin) / bbox.resolution[1])

        params = dict(
            service='WMS',
            version='1.3.0',
            request="GetMap",
            layers=str(self),
            time=bbox.time_str,
            crs=bbox.srs,
            bbox=bbox.bbox_ogc_str,
            width=width,
            height=height,
            format='image/png',
            styles=colorizer.to_query_string(),
        )

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
        resolution = str(f'{bbox.resolution[0]},{bbox.resolution[1]}')

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
    ) -> DataArray:
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
            assert isinstance(data_array, DataArray)

            rio: DataArray = data_array.rio
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

    def get_provenance(self, timeout: int = 60) -> List[ProvenanceOutput]:
        '''
        Query the provenance of the workflow
        '''

        session = get_session()

        provenance_url = f'{session.server_url}/workflow/{self.__workflow_id}/provenance'

        response = req.get(provenance_url, headers=session.auth_header, timeout=timeout).json()

        return [ProvenanceOutput.from_response(item) for item in response]

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
            bbox: QueryRectangle,
            name: str,
            description: str = '',
            timeout: int = 3600) -> Task:
        '''Init task to store the workflow result as a layer'''

        # Currently, it only works for raster results
        if not self.__result_descriptor.is_raster_result():
            raise MethodNotCalledOnRasterException()

        # The dataset is created in the spatial reference system of the workflow result
        if self.get_result_descriptor().spatial_reference != bbox.srs:
            raise SpatialReferenceMismatchException(
                self.get_result_descriptor().spatial_reference,
                bbox.srs
            )

        session = get_session()

        request_body = {
            'name': name,
            'description': description,
            'query': bbox.__dict__(),
        }

        response = req.post(
            url=f'{session.server_url}/datasetFromWorkflow/{self.__workflow_id}',
            json=request_body,
            headers=session.auth_header,
            timeout=timeout
        )

        check_response_for_error(response)

        return Task(TaskId.from_response(response.json()))


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
