from __future__ import annotations
from enum import Enum
from attr import dataclass
from numpy import number
from geoengine.error import GeoEngineException, InputException, TypeException
from typing import Any, Dict, Tuple
from datetime import datetime


class QueryRectangle:
    '''
    A multi-dimensional query rectangle, consisting of spatial and temporal information.
    '''

    __spatial_bounds: Tuple[float, float, float, float]
    __time_interval: Tuple[datetime, datetime]
    __resolution: Tuple[float, float]
    __srs: str

    def __init__(self, spatial_bounds: Tuple[float, float, float, float], time_interval: Tuple[datetime, datetime], resolution: Tuple[float, float] = [0.1, 0.1], srs='EPSG:4326') -> None:
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
        return ','.join(map(str, self.__spatial_bounds))

    @property
    def bbox_ogc(self) -> str:
        # TODO: properly handle axis order
        bbox = self.__spatial_bounds
        if self.__srs == "EPSG:4326":
            return [bbox[1], bbox[0], bbox[3], bbox[2]]
        else:
            return bbox

    @property
    def resolution_ogc(self) -> Tuple[float, float]:
        # TODO: properly handle axis order
        res = self.__resolution
        if self.__srs == "EPSG:4326":
            return [-res[1], res[0]]
        else:
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
        if self.__time_interval[0] == self.__time_interval[1]:
            return self.__time_interval[0].isoformat(timespec='milliseconds')

        return '/'.join(map(str, self.__time_interval))

    @property
    def resolution(self) -> Tuple[float, float]:
        return self.__resolution

    @property
    def srs(self) -> str:
        return self.__srs


class ResultDescriptor:
    @staticmethod
    def from_response(response: Dict[str, Any]) -> None:

        if 'error' in response:
            raise GeoEngineException(response)

        result_descriptor_type = response['type']

        if result_descriptor_type == 'raster':
            return RasterResultDescriptor(response)
        elif result_descriptor_type == 'vector':
            return VectorResultDescriptor(response)
        elif result_descriptor_type == 'plot':
            return PlotResultDescriptor(response)
        else:
            raise TypeException(
                f'Unknown `ResultDescriptor` type: {result_descriptor_type}')


class VectorResultDescriptor(ResultDescriptor):
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

    @property
    def data_type(self) -> str:
        return self.__data_type

    @property
    def spatial_reference(self) -> str:
        return self.__spatial_reference

    @property
    def columns(self) -> Dict[str, str]:
        return self.__columns


class RasterResultDescriptor(ResultDescriptor):
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
    def __init__(self, _response: Dict[str, Any]) -> None:
        pass

    def __repr__(self) -> str:
        r = 'Plot Result'

        return r


class VectorDataType(Enum):
    data = 'Data'
    multi_point = 'MultiPoint'
    multi_line_string = 'MultiLineString'
    multi_polygon = 'MultiPolygon'

    @classmethod
    def from_geopandas_type_name(cls, name: str) -> VectorDataType:
        name_map = {
            "Point": VectorDataType.multi_point,
            "MultiPoint": VectorDataType.multi_point,
            "Line": VectorDataType.multi_line_string,
            "MultiLine": VectorDataType.multi_line_string,
            "Polygon": VectorDataType.multi_polygon,
            "MultiPolygon": VectorDataType.multi_polygon,
        }

        if name in name_map:
            return name_map[name]

        raise InputException("Invalid vector data type")


class TimeStepGranularity(Enum):
    millis = 'Millis'
    seconds = 'Seconds'
    minutes = 'Minutes'
    hours = 'Hours'
    days = 'Days'
    months = 'Months'
    years = 'Years'


@dataclass
class TimeStep:
    step: int
    granularity: TimeStepGranularity
