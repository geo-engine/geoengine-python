'''
Different type mappings of geo engine types
'''

from __future__ import annotations
from typing import Any, Dict, Tuple
from datetime import datetime
from uuid import UUID

from enum import Enum
from attr import dataclass
from numpy import number

from geoengine.error import GeoEngineException, InputException, TypeException


class QueryRectangle:
    '''
    A multi-dimensional query rectangle, consisting of spatial and temporal information.
    '''

    __spatial_bounds: Tuple[float, float, float, float]
    __time_interval: Tuple[datetime, datetime]
    __resolution: Tuple[float, float]
    __srs: str

    def __init__(self,
                 spatial_bounds: Tuple[float, float, float, float],
                 time_interval: Tuple[datetime, datetime],
                 resolution: Tuple[float, float] = (0.1, 0.1),
                 srs='EPSG:4326') -> None:
        xmin = spatial_bounds[0]
        ymin = spatial_bounds[1]
        xmax = spatial_bounds[2]
        ymax = spatial_bounds[3]

        if (xmin > xmax) or (ymin > ymax):
            raise InputException("Bbox: Malformed since min must be <= max")

        self.__spatial_bounds = spatial_bounds

        if time_interval[0] > time_interval[1]:
            raise InputException("Time inverval: Start must be <= End")

        self.__time_interval = time_interval

        if resolution[0] <= 0 or resolution[1] <= 0:
            raise InputException("Resolution: Must be positive")

        self.__resolution = resolution

        self.__srs = srs

    @property
    def bbox_str(self) -> str:
        '''
        A comma-separated string representation of the spatial bounds
        '''

        return ','.join(map(str, self.__spatial_bounds))

    @property
    def bbox_ogc_str(self) -> str:
        '''
        A comma-separated string representation of the spatial bounds with OGC axis ordering
        '''

        return ','.join(map(str, self.bbox_ogc))

    @property
    def bbox_ogc(self) -> Tuple[float, float, float, float]:
        '''
        Return the bbox with OGC axis ordering of the srs
        '''

        # TODO: properly handle axis order
        bbox = self.__spatial_bounds

        if self.__srs == "EPSG:4326":
            return (bbox[1], bbox[0], bbox[3], bbox[2])

        return bbox

    @property
    def resolution_ogc(self) -> Tuple[float, float]:
        '''
        Return the resolution in OGC style
        '''

        # TODO: properly handle axis order
        res = self.__resolution

        if self.__srs == "EPSG:4326":
            return [-res[1], res[0]]

        return res

    @property
    def xmin(self) -> number:
        return self.__spatial_bounds[0]

    @property
    def ymin(self) -> number:
        return self.__spatial_bounds[1]

    @property
    def xmax(self) -> number:
        return self.__spatial_bounds[2]

    @property
    def ymax(self) -> number:
        return self.__spatial_bounds[3]

    @property
    def time_str(self) -> str:
        '''
        Return the time instance or interval as a string representation
        '''

        if self.__time_interval[0] == self.__time_interval[1]:
            return self.__time_interval[0].isoformat(timespec='milliseconds')

        return '/'.join(map(str, self.__time_interval))

    @property
    def resolution(self) -> Tuple[float, float]:
        '''
        Return the resolution as is
        '''

        return self.__resolution

    @property
    def srs(self) -> str:
        '''
        Return the SRS string
        '''

        return self.__srs


class ResultDescriptor:  # pylint: disable=too-few-public-methods
    '''
    Base class for result descriptors
    '''

    @staticmethod
    def from_response(response: Dict[str, Any]) -> None:
        '''
        Parse a result descriptor from an http response
        '''

        if 'error' in response:
            raise GeoEngineException(response)

        result_descriptor_type = response['type']

        if result_descriptor_type == 'raster':
            return RasterResultDescriptor(response)
        if result_descriptor_type == 'vector':
            return VectorResultDescriptor(response)
        if result_descriptor_type == 'plot':
            return PlotResultDescriptor(response)

        raise TypeException(
            f'Unknown `ResultDescriptor` type: {result_descriptor_type}')

    @classmethod
    def is_raster_result(cls) -> bool:
        '''
        Return true if the result is of type raster
        '''

        return False

    @classmethod
    def is_vector_result(cls) -> bool:
        '''
        Return true if the result is of type vector
        '''

        return False

    @classmethod
    def is_plot_result(cls) -> bool:
        '''
        Return true if the result is of type plot
        '''

        return False


class VectorResultDescriptor(ResultDescriptor):
    '''
    A vector result descriptor
    '''

    __data_type: str
    __spatial_reference: str
    __columns: Dict[str, str]

    def __init__(self, response: Dict[str, Any]) -> None:
        self.__data_type = response['dataType']
        self.__spatial_reference = response['spatialReference']
        self.__columns = response['columns']

    def __repr__(self) -> str:
        r = ''
        r += f'Data type:         {self.data_type}\n'
        r += f'Spatial Reference: {self.spatial_reference}\n'

        for i, key in enumerate(self.columns):
            r += 'Columns:' if i == 0 else '        '
            r += '           '
            r += f'{key}: {self.columns[key]}\n'

        return r

    @classmethod
    def is_vector_result(cls) -> bool:
        return True

    @property
    def data_type(self) -> str:
        '''Return the data type'''

        return self.__data_type

    @property
    def spatial_reference(self) -> str:
        '''Return the spatial reference'''

        return self.__spatial_reference

    @property
    def columns(self) -> Dict[str, str]:
        '''Return the columns'''

        return self.__columns


class RasterResultDescriptor(ResultDescriptor):
    '''
    A raster result descriptor
    '''

    __data_type: str
    __spatial_reference: str
    __measurement: str
    __no_data_value: str

    def __init__(self, response: Dict[str, Any]) -> None:
        self.__data_type = response['dataType']
        self.__spatial_reference = response['spatialReference']
        self.__measurement = response['measurement']
        self.__no_data_value = response['noDataValue']

    def __repr__(self) -> str:
        r = ''
        r += f'Data type:         {self.data_type}\n'
        r += f'Spatial Reference: {self.spatial_reference}\n'
        r += f'Measurement:       {self.measurement}\n'
        r += f'No Data Value:     {self.no_data_value}\n'

        return r

    @classmethod
    def is_raster_result(cls) -> bool:
        return True

    @property
    def data_type(self) -> str:
        return self.__data_type

    @property
    def spatial_reference(self) -> str:
        return self.__spatial_reference

    @property
    def measurement(self) -> str:
        return self.__measurement

    @property
    def no_data_value(self) -> str:
        return self.__no_data_value


class PlotResultDescriptor(ResultDescriptor):
    '''
    A plot result descriptor
    '''

    def __init__(self, _response: Dict[str, Any]) -> None:
        pass

    def __repr__(self) -> str:
        r = 'Plot Result'

        return r

    @classmethod
    def is_plot_result(cls) -> bool:
        return True


class VectorDataType(Enum):
    '''An enum of vector data types'''

    DATA = 'Data'
    MULTI_POINT = 'MultiPoint'
    MULTI_LINE_STRING = 'MultiLineString'
    MULTI_POLYGON = 'MultiPolygon'

    @classmethod
    def from_geopandas_type_name(cls, name: str) -> VectorDataType:
        '''Resolve vector data type from geopandas geometry type'''

        name_map = {
            "Point": VectorDataType.MULTI_POINT,
            "MultiPoint": VectorDataType.MULTI_POINT,
            "Line": VectorDataType.MULTI_LINE_STRING,
            "MultiLine": VectorDataType.MULTI_LINE_STRING,
            "Polygon": VectorDataType.MULTI_POLYGON,
            "MultiPolygon": VectorDataType.MULTI_POLYGON,
        }

        if name in name_map:
            return name_map[name]

        raise InputException("Invalid vector data type")


class TimeStepGranularity(Enum):
    '''An enum of time step granularities'''
    MILLIS = 'Millis'
    SECONDS = 'Seconds'
    MINUTES = 'Minutes'
    HOURS = 'Hours'
    DAYS = 'Days'
    MONTHS = 'Months'
    YEARS = 'Years'


@dataclass
class TimeStep:
    '''A time step that consists of a granularity and a step size'''
    step: int
    granularity: TimeStepGranularity


@dataclass
class Provenance:
    '''Provenance information as triplet of citation, license and uri'''

    citation: str
    license: str
    uri: str

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> Provenance:
        '''Parse an http response to a `Provenance` object'''
        return Provenance(response['citation'], response['license'], response['uri'])


@dataclass
class ProvenanceOutput:
    '''Provenance of a dataset'''

    dataset: DatasetId
    provenance: Provenance

    @classmethod
    def from_response(cls, response: Dict[str, Dict[str, str]]) -> ProvenanceOutput:
        '''Parse an http response to a `ProvenanceOutput` object'''

        dataset = DatasetId.from_response(response['dataset'])
        provenance = Provenance.from_response(response['provenance'])

        return ProvenanceOutput(dataset, provenance)


class DatasetId:  # pylint: disable=too-few-public-methods
    '''Base class for dataset ids'''
    @classmethod
    def from_response(cls, response: Dict[str, str]) -> DatasetId:
        '''Parse an http response to a `DatasetId` object'''

        if response["type"] == "internal":
            return InternalDatasetId.from_response(response)
        if response["type"] == "external":
            return ExternalDatasetId.from_response(response)

        raise GeoEngineException(f"Unknown DatasetId type: {response['type']}")


class InternalDatasetId(DatasetId):
    '''An internal dataset id'''

    __dataset_id: UUID

    def __init__(self, dataset_id: UUID):
        self.__dataset_id = dataset_id

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> InternalDatasetId:
        '''Parse an http response to a `InternalDatasetId` object'''

        return InternalDatasetId(response['datasetId'])

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "internal",
            "datasetId": self.__dataset_id
        }

    def __str__(self) -> str:
        return str(self.__dataset_id)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return self.__dataset_id == other.__dataset_id  # pylint: disable=protected-access


class ExternalDatasetId(DatasetId):
    '''An external dataset id'''

    __provider_id: UUID
    __dataset_id: str

    def __init__(self, provider_id: UUID, dataset_id: str):
        self.__provider_id = provider_id
        self.__dataset_id = dataset_id

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> ExternalDatasetId:
        '''Parse an http response to a `ExternalDatasetId` object'''

        return ExternalDatasetId(response['providerId'], response['datasetId'])

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "external",
            "providerId": self.__provider_id,
            "datasetId": self.__dataset_id,
        }

    def __str__(self) -> str:
        return f'{self.__provider_id}:{self.__dataset_id}'

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return self.__provider_id == other.__provider_id and self.__dataset_id == other.__dataset_id  # pylint: disable=protected-access
