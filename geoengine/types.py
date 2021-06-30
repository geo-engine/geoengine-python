from numpy import number
from geoengine.error import GeoEngineException, InputException, TypeException
from typing import Any, Dict, Tuple
from datetime import datetime


class Bbox:
    '''
    A multi-dimensional bounding box, consisting of spatial and temporal information.
    '''

    __spatial_bbox: Tuple[float, float, float, float]
    __time_interval: Tuple[datetime, datetime]
    __resolution: float
    __srs: str

    def __init__(self, spatial_bbox: Tuple[float, float, float, float], time_interval: Tuple[datetime, datetime], resolution=0.1, srs='EPSG:4326') -> None:
        xmin = spatial_bbox[0]
        ymin = spatial_bbox[1]
        xmax = spatial_bbox[2]
        ymax = spatial_bbox[3]

        if (xmin > xmax) or (ymin > ymax):
            raise InputException("Bbox: Malformed since min must be <= max")

        self.__spatial_bbox = spatial_bbox

        if time_interval[0] > time_interval[1]:
            raise InputException("Time inverval: Start must be <= End")

        self.__time_interval = time_interval

        if resolution <= 0:
            raise InputException("Resoultion: Must be positive")

        self.__resolution = resolution

        self.__srs = srs

    @property
    def bbox_str(self) -> str:
        return ','.join(map(str, self.__spatial_bbox))

    @property
    def xmin(self) -> number:
        return self.__spatial_bbox[0]

    @property
    def ymin(self) -> number:
        return self.__spatial_bbox[1]

    @property
    def xmax(self) -> number:
        return self.__spatial_bbox[2]

    @property
    def ymax(self) -> number:
        return self.__spatial_bbox[3]

    @property
    def time_str(self) -> str:
        if self.__time_interval[0] == self.__time_interval[1]:
            return self.__time_interval[0].isoformat(timespec='milliseconds')

        return '/'.join(map(str, self.__time_interval))

    @property
    def resolution(self) -> float:
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
