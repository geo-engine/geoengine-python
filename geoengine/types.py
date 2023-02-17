# pylint: disable=too-many-lines

'''
Different type mappings of geo engine types
'''

from __future__ import annotations
from abc import abstractmethod
from datetime import datetime
from uuid import UUID
from enum import Enum
from typing import Dict, Optional, Tuple, cast, List
from typing_extensions import Literal
from attr import dataclass
from geoengine.colorizer import Colorizer
from geoengine import api
from geoengine.error import GeoEngineException, InputException, TypeException

DEFAULT_ISO_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"


class SpatialBounds:
    '''A spatial bounds object'''
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __init__(self, xmin: float, ymin: float, xmax: float, ymax: float) -> None:
        '''Initialize a new `SpatialBounds` object'''
        if (xmin > xmax) or (ymin > ymax):
            raise InputException("Bbox: Malformed since min must be <= max")

        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    def as_bbox_str(self, y_axis_first=False) -> str:
        '''
        A comma-separated string representation of the spatial bounds with OGC axis ordering
        '''
        bbox_tuple = self.as_bbox_tuple(y_axis_first=y_axis_first)
        return f'{bbox_tuple[0]},{bbox_tuple[1]},{bbox_tuple[2]},{bbox_tuple[3]}'

    def as_bbox_tuple(self, y_axis_first=False) -> Tuple[float, float, float, float]:
        '''
        Return the bbox with OGC axis ordering of the srs
        '''

        if y_axis_first:
            return (self.ymin, self.xmin, self.ymax, self.xmax)

        return (self.xmin, self.ymin, self.xmax, self.ymax)

    def x_axis_size(self) -> float:
        '''The size of the x axis'''
        return self.xmax - self.xmin

    def y_axis_size(self) -> float:
        '''The size of the y axis'''
        return self.ymax - self.ymin


class BoundingBox2D(SpatialBounds):
    ''''A 2D bounding box.'''

    def to_api_dict(self) -> api.BoundingBox2D:
        return api.BoundingBox2D({
            'lowerLeftCoordinate': api.Coordinate2D({
                "x": self.xmin,
                "y": self.ymin,
            }),
            'upperRightCoordinate': api.Coordinate2D({
                "x": self.xmax,
                "y": self.ymax,
            }),
        })

    @staticmethod
    def from_response(response: api.BoundingBox2D) -> BoundingBox2D:
        '''create a `BoundingBox2D` from an API response'''
        if 'lowerLeftCoordinate' not in response or 'upperRightCoordinate' not in response:
            raise TypeException('BoundingBox2D must have lowerLeftCoordinate and upperRightCoordinate')

        lower_left = response['lowerLeftCoordinate']
        upper_right = response['upperRightCoordinate']

        return BoundingBox2D(
            lower_left['x'],
            lower_left['y'],
            upper_right['x'],
            upper_right['y'],
        )

    def __repr__(self) -> str:
        return f'BoundingBox2D(xmin={self.xmin}, ymin={self.ymin}, xmax={self.xmax}, ymax={self.ymax})'


class SpatialPartition2D(SpatialBounds):
    '''A 2D spatial partition.'''

    @staticmethod
    def from_response(response: api.SpatialPartition2D) -> SpatialPartition2D:
        '''create a `SpatialPartition2D` from an API response'''
        if 'upperLeftCoordinate' not in response or 'lowerRightCoordinate' not in response:
            raise TypeException('SpatialPartition2D must have upperLeftCoordinate and lowerRightCoordinate')

        upper_left = response['upperLeftCoordinate']
        lower_right = response['lowerRightCoordinate']

        return SpatialPartition2D(
            upper_left['x'],
            lower_right['y'],
            lower_right['x'],
            upper_left['y'],

        )

    def to_api_dict(self) -> api.SpatialPartition2D:
        return api.SpatialPartition2D({
            'upperLeftCoordinate': api.Coordinate2D({
                "x": self.xmin,
                "y": self.ymax,
            }),
            'lowerRightCoordinate': api.Coordinate2D({
                "x": self.xmax,
                "y": self.ymin,
            }),
        })

    def to_bounding_box(self) -> BoundingBox2D:
        '''convert to a `BoundingBox2D`'''
        return BoundingBox2D(self.xmin, self.ymin, self.xmax, self.ymax)


class TimeInterval:
    ''''A time interval.'''
    start: datetime
    end: Optional[datetime]

    def __init__(self, start: datetime, end: Optional[datetime] = None) -> None:
        '''Initialize a new `TimeInterval` object'''
        if end is not None and start > end:
            raise InputException("Time inverval: Start must be <= End")
        self.start = start
        self.end = end

    def is_instant(self) -> bool:
        return self.end is None

    def to_api_dict(self, as_millis=False) -> api.TimeInterval:
        '''convert to a dict that can be used in the API'''
        if as_millis:
            return api.TimeInterval({
                'start': int(self.start.timestamp() * 1000),
                'end': int(self.end.timestamp() * 1000) if self.end is not None else None,
            })

        return api.TimeInterval({
            'start': self.start.isoformat(timespec='milliseconds'),
            'end': self.end.isoformat(timespec='milliseconds') if self.end is not None else None,
        })

    @property
    def time_str(self) -> str:
        '''
        Return the time instance or interval as a string representation
        '''
        if self.end is None or self.start == self.end:
            return self.start.isoformat(timespec='milliseconds')
        return self.start.isoformat(timespec='milliseconds') + '/' + self.end.isoformat(timespec='milliseconds')

    @staticmethod
    def from_response(response: api.TimeInterval) -> TimeInterval:
        '''create a `TimeInterval` from an API response'''

        if 'start' not in response:
            raise TypeException('TimeInterval must have a start')

        if isinstance(response['start'], int):
            start = cast(int, response['start'])
            end = cast(int, response['end']) if 'end' in response and response['end'] is not None else None

            return TimeInterval(
                datetime.fromtimestamp(start / 1000),
                datetime.fromtimestamp(end / 1000) if end is not None else None,
            )

        start_str = cast(str, response['start'])
        end_str = cast(str, response['end']) if 'end' in response and response['end'] is not None else None

        return TimeInterval(
            datetime.fromisoformat(start_str),
            datetime.fromisoformat(end_str) if end_str is not None else None,
        )

    def __repr__(self) -> str:
        return f"TimeInterval(start={self.start}, end={self.end})"


class SpatialResolution:
    ''''A spatial resolution.'''
    x_resolution: float
    y_resolution: float

    def __init__(self, x_resolution: float, y_resolution: float) -> None:
        '''Initialize a new `SpatialResolution` object'''
        if x_resolution <= 0 or y_resolution <= 0:
            raise InputException("Resolution: Must be positive")

        self.x_resolution = x_resolution
        self.y_resolution = y_resolution

    def to_api_dict(self) -> api.SpatialResolution:
        return api.SpatialResolution({
            'x': self.x_resolution,
            'y': self.y_resolution,
        })

    @staticmethod
    def from_response(response: api.SpatialResolution) -> SpatialResolution:
        '''create a `SpatialResolution` from an API response'''
        return SpatialResolution(x_resolution=response['x'], y_resolution=response['y'])

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x_resolution, self.y_resolution)

    def __str__(self) -> str:
        return str(f'{self.x_resolution},{self.y_resolution}')

    def __repr__(self) -> str:
        return str(f'SpatialResolution(x={self.x_resolution}, y={self.y_resolution})')


class QueryRectangle:
    '''
    A multi-dimensional query rectangle, consisting of spatial and temporal information.
    '''

    __spatial_bounds: BoundingBox2D
    __time_interval: TimeInterval
    __resolution: SpatialResolution
    __srs: str

    def __init__(self,
                 spatial_bounds: BoundingBox2D,
                 time_interval: TimeInterval,
                 resolution: SpatialResolution,
                 srs='EPSG:4326') -> None:
        '''Initialize a new `QueryRectangle` object'''
        self.__spatial_bounds = spatial_bounds
        self.__time_interval = time_interval
        self.__resolution = resolution
        self.__srs = srs

    @property
    def bbox_str(self) -> str:
        '''
        A comma-separated string representation of the spatial bounds
        '''
        return self.__spatial_bounds.as_bbox_str()

    @property
    def bbox_ogc_str(self) -> str:
        '''
        A comma-separated string representation of the spatial bounds with OGC axis ordering
        '''
        y_axis_first = self.__srs == "EPSG:4326"
        return self.__spatial_bounds.as_bbox_str(y_axis_first=y_axis_first)

    @property
    def bbox_ogc(self) -> Tuple[float, float, float, float]:
        '''
        Return the bbox with OGC axis ordering of the srs
        '''

        # TODO: properly handle axis order
        y_axis_first = self.__srs == "EPSG:4326"
        return self.__spatial_bounds.as_bbox_tuple(y_axis_first=y_axis_first)

    @property
    def resolution_ogc(self) -> Tuple[float, float]:
        '''
        Return the resolution in OGC style
        '''
        # TODO: properly handle axis order
        res = self.__resolution

        # TODO: why is the y resolution in this case negative but not in all other cases?
        if self.__srs == "EPSG:4326":
            return (-res.y_resolution, res.x_resolution)

        return res.as_tuple()

    @property
    def time(self) -> TimeInterval:
        '''
        Return the time instance or interval
        '''
        return self.__time_interval

    @property
    def spatial_bounds(self) -> BoundingBox2D:
        '''
        Return the spatial bounds
        '''
        return self.__spatial_bounds

    @property
    def spatial_resolution(self) -> SpatialResolution:
        '''
        Return the spatial resolution
        '''
        return self.__resolution

    @property
    def time_str(self) -> str:
        '''
        Return the time instance or interval as a string representation
        '''
        return self.time.time_str

    @property
    def srs(self) -> str:
        '''
        Return the SRS string
        '''
        return self.__srs

    def __repr__(self) -> str:
        ''' Return a string representation of the query rectangle.'''
        r = 'QueryRectangle( \n'
        r += '    ' + repr(self.__spatial_bounds) + '\n'
        r += '    ' + repr(self.__time_interval) + '\n'
        r += '    ' + repr(self.__resolution) + '\n'
        r += f'    srs={self.__srs} \n'
        r += ')'
        return r


class ResultDescriptor:  # pylint: disable=too-few-public-methods
    '''
    Base class for result descriptors
    '''

    __spatial_reference: str
    __time_bounds: Optional[TimeInterval]
    __spatial_resolution: Optional[SpatialResolution]

    def __init__(
        self,
        spatial_reference: str,
        time_bounds: Optional[TimeInterval] = None,
        spatial_resolution: Optional[SpatialResolution] = None
    ) -> None:
        '''Initialize a new `ResultDescriptor` object'''

        self.__spatial_reference = spatial_reference
        self.__time_bounds = time_bounds

        if spatial_resolution is None or isinstance(spatial_resolution, SpatialResolution):
            self.__spatial_resolution = spatial_resolution
        else:
            raise TypeException('Spatial resolution must be of type `SpatialResolution` or `None`')

    @staticmethod
    def from_response(response: api.ResultDescriptor) -> ResultDescriptor:
        '''
        Parse a result descriptor from an http response
        '''

        if 'error' in response:
            raise GeoEngineException(cast(api.GeoEngineExceptionResponse, response))

        if 'type' not in response:
            raise TypeException('Response does not contain a `type` field')

        result_descriptor_type = response['type']

        if result_descriptor_type == 'raster':
            return RasterResultDescriptor.from_response_raster(cast(api.RasterResultDescriptor, response))
        if result_descriptor_type == 'vector':
            return VectorResultDescriptor.from_response_vector(cast(api.VectorResultDescriptor, response))
        if result_descriptor_type == 'plot':
            return PlotResultDescriptor.from_response_plot(cast(api.PlotResultDescriptor, response))

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

    @property
    def spatial_reference(self) -> str:
        '''Return the spatial reference'''

        return self.__spatial_reference

    @property
    def time_bounds(self) -> Optional[TimeInterval]:
        '''Return the time bounds'''

        return self.__time_bounds

    @property
    def spatial_resolution(self) -> Optional[SpatialResolution]:
        '''Return the spatial resolution'''

        return self.__spatial_resolution

    @abstractmethod
    def to_api_dict(self) -> api.ResultDescriptor:
        pass

    def __iter__(self):
        return iter(self.to_api_dict().items())


class VectorResultDescriptor(ResultDescriptor):
    '''
    A vector result descriptor
    '''
    __spatial_bounds: Optional[BoundingBox2D]
    __data_type: VectorDataType
    __columns: Dict[str, VectorColumnInfo]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        spatial_reference: str,
        data_type: VectorDataType,
        columns: Dict[str, VectorColumnInfo],
        time_bounds: Optional[TimeInterval] = None,
        spatial_bounds: Optional[BoundingBox2D] = None,
        spatial_resolution: Optional[SpatialResolution] = None
    ) -> None:
        ''' Initialize a vector result descriptor '''
        super().__init__(spatial_reference, time_bounds, spatial_resolution)
        self.__data_type = data_type
        self.__columns = columns
        self.__spatial_bounds = spatial_bounds

    @staticmethod
    def from_response_vector(response: api.VectorResultDescriptor) -> VectorResultDescriptor:
        '''Parse a vector result descriptor from an http response'''
        assert response['type'] == 'vector'  # TODO: throw exception

        sref = response['spatialReference']
        data_type = VectorDataType.from_string(response['dataType'])
        columns = {name: VectorColumnInfo.from_response(info) for name, info in response['columns'].items()}

        time_bounds = None
        # FIXME: datetime can not represent our min max range
        # if 'time' in response and response['time'] is not None:
        #    time_bounds = TimeInterval.from_response(response['time'])
        spatial_bounds = None
        if 'bbox' in response and response['bbox'] is not None:
            spatial_bounds = BoundingBox2D.from_response(response['bbox'])
        spatial_resolution = None
        if 'resolution' in response and response['resolution'] is not None:
            spatial_resolution = SpatialResolution.from_response(response['resolution'])

        return VectorResultDescriptor(sref, data_type, columns, time_bounds, spatial_bounds, spatial_resolution)

    @classmethod
    def is_vector_result(cls) -> bool:
        return True

    @property
    def data_type(self) -> VectorDataType:
        '''Return the data type'''
        return self.__data_type

    @property
    def spatial_reference(self) -> str:
        '''Return the spatial reference'''
        return super().spatial_reference

    @property
    def columns(self) -> Dict[str, VectorColumnInfo]:
        '''Return the columns'''

        return self.__columns

    @property
    def spatial_bounds(self) -> Optional[BoundingBox2D]:
        '''Return the spatial bounds'''
        return self.__spatial_bounds

    def __repr__(self) -> str:
        '''Display representation of the vector result descriptor'''
        r = ''
        r += f'Data type:         {self.data_type}\n'
        r += f'Spatial Reference: {self.spatial_reference}\n'

        r += 'Columns:\n'
        for column_name in self.columns:
            column_info = self.columns[column_name]
            r += f'  {column_name}:\n'
            r += f'    Column Type: {column_info.data_type}\n'
            r += f'    Measurement: {column_info.measurement}\n'

        return r

    def to_api_dict(self) -> api.VectorResultDescriptor:
        '''Convert the vector result descriptor to a dictionary'''

        return api.VectorResultDescriptor({
            'type': 'raster',
            'dataType': self.data_type.to_api_enum(),
            'spatialReference': self.spatial_reference,
            'columns':
                {name: column_info.to_api_dict() for name, column_info in self.columns.items()},
            'time': self.time_bounds.to_api_dict() if self.time_bounds is not None else None,
            'bbox': self.spatial_bounds.to_api_dict() if self.spatial_bounds is not None else None,
            'resolution': self.spatial_resolution.to_api_dict() if self.spatial_resolution is not None else None,
        })


@dataclass
class VectorColumnInfo:
    '''Vector column information'''

    data_type: str
    measurement: Measurement

    @staticmethod
    def from_response(response: api.VectorColumnInfo) -> VectorColumnInfo:
        '''Create a new `VectorColumnInfo` from a JSON response'''

        return VectorColumnInfo(response['dataType'], Measurement.from_response(response['measurement']))

    def to_api_dict(self) -> api.VectorColumnInfo:
        '''Convert to a dictionary'''

        return api.VectorColumnInfo({
            'dataType': self.data_type,
            'measurement': self.measurement.to_api_dict(),
        })


class RasterResultDescriptor(ResultDescriptor):
    '''
    A raster result descriptor
    '''
    __data_type: Literal['U8', 'U16', 'U32', 'U64', 'I8', 'I16', 'I32', 'I64', 'F32', 'F64']
    __measurement: Measurement
    __spatial_bounds: Optional[SpatialPartition2D]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        data_type: Literal['U8', 'U16', 'U32', 'U64', 'I8', 'I16', 'I32', 'I64', 'F32', 'F64'],
        measurement: Measurement,
        spatial_reference: str,
        time_bounds: Optional[TimeInterval] = None,
        spatial_bounds: Optional[SpatialPartition2D] = None,
        spatial_resolution: Optional[SpatialResolution] = None
    ) -> None:
        '''Initialize a new `RasterResultDescriptor`'''
        super().__init__(spatial_reference, time_bounds, spatial_resolution)
        self.__data_type = data_type
        self.__measurement = measurement
        self.__spatial_bounds = spatial_bounds

    def to_api_dict(self) -> api.RasterResultDescriptor:
        '''Convert the raster result descriptor to a dictionary'''

        return {
            'type': 'raster',
            'dataType': self.data_type,
            'measurement': self.measurement.to_api_dict(),
            'spatialReference': self.spatial_reference,
            'time': self.time_bounds.to_api_dict() if self.time_bounds is not None else None,
            'bbox': self.spatial_bounds.to_api_dict() if self.spatial_bounds is not None else None,
            'resolution': self.spatial_resolution.to_api_dict() if self.spatial_resolution is not None else None
        }

    @staticmethod
    def from_response_raster(response: api.RasterResultDescriptor) -> RasterResultDescriptor:
        '''Parse a raster result descriptor from an http response'''
        assert response['type'] == 'raster'  # TODO: throw exception

        spatial_ref = response['spatialReference']
        data_type = response['dataType']
        measurement = Measurement.from_response(response['measurement'])

        time_bounds = None
        # FIXME: datetime can not represent our min max range
        # if 'time' in response and response['time'] is not None:
        #    time_bounds = TimeInterval.from_response(response['time'])
        spatial_bounds = None
        if 'bbox' in response and response['bbox'] is not None:
            spatial_bounds = SpatialPartition2D.from_response(response['bbox'])
        spatial_resolution = None
        if 'resolution' in response and response['resolution'] is not None:
            spatial_resolution = SpatialResolution.from_response(response['resolution'])

        return RasterResultDescriptor(
            data_type=data_type,
            measurement=measurement,
            spatial_reference=spatial_ref,
            time_bounds=time_bounds,
            spatial_bounds=spatial_bounds,
            spatial_resolution=spatial_resolution
        )

    @classmethod
    def is_raster_result(cls) -> bool:
        return True

    @property
    def data_type(self) -> Literal['U8', 'U16', 'U32', 'U64', 'I8', 'I16', 'I32', 'I64', 'F32', 'F64']:
        return self.__data_type

    @property
    def measurement(self) -> Measurement:
        return self.__measurement

    @property
    def spatial_bounds(self) -> Optional[SpatialPartition2D]:
        return self.__spatial_bounds

    @property
    def spatial_reference(self) -> str:
        '''Return the spatial reference'''

        return super().spatial_reference

    def __repr__(self) -> str:
        '''Display representation of the raster result descriptor'''
        r = ''
        r += f'Data type:         {self.data_type}\n'
        r += f'Spatial Reference: {self.spatial_reference}\n'
        r += f'Measurement:       {self.measurement}\n'

        return r

    def to_json(self) -> api.RasterResultDescriptor:
        return self.to_api_dict()


class PlotResultDescriptor(ResultDescriptor):
    '''
    A plot result descriptor
    '''

    __spatial_bounds: Optional[BoundingBox2D]

    def __init__(  # pylint: disable=too-many-arguments]
        self,
        spatial_reference: str,
        time_bounds: Optional[TimeInterval] = None,
        spatial_bounds: Optional[BoundingBox2D] = None,
        spatial_resolution: Optional[SpatialResolution] = None
    ) -> None:
        '''Initialize a new `PlotResultDescriptor`'''
        super().__init__(spatial_reference, time_bounds, spatial_resolution)
        self.__spatial_bounds = spatial_bounds

    def __repr__(self) -> str:
        '''Display representation of the plot result descriptor'''
        r = 'Plot Result'

        return r

    @staticmethod
    def from_response_plot(response: api.PlotResultDescriptor) -> PlotResultDescriptor:
        '''Create a new `PlotResultDescriptor` from a JSON response'''
        assert response['type'] == 'plot'  # TODO: throw exception

        spatial_ref = response['spatialReference']

        time_bounds = None
        # FIXME: datetime can not represent our min max range
        # if 'time' in response and response['time'] is not None:
        #    time_bounds = TimeInterval.from_response(response['time'])
        spatial_bounds = None
        if 'bbox' in response and response['bbox'] is not None:
            spatial_bounds = BoundingBox2D.from_response(response['bbox'])
        spatial_resolution = None
        if 'resolution' in response and response['resolution'] is not None:
            spatial_resolution = SpatialResolution.from_response(response['resolution'])

        return PlotResultDescriptor(
            spatial_reference=spatial_ref,
            time_bounds=time_bounds,
            spatial_bounds=spatial_bounds,
            spatial_resolution=spatial_resolution
        )

    @classmethod
    def is_plot_result(cls) -> bool:
        return True

    @property
    def spatial_reference(self) -> str:
        '''Return the spatial reference'''
        return super().spatial_reference

    @property
    def spatial_bounds(self) -> Optional[BoundingBox2D]:
        return self.__spatial_bounds

    def to_api_dict(self) -> api.PlotResultDescriptor:
        '''Convert the plot result descriptor to a dictionary'''

        return api.PlotResultDescriptor({
            'type': 'plot',
            'spatialReference': self.spatial_reference,
            'dataType': 'Plot',
            'time': self.time_bounds.to_api_dict() if self.time_bounds is not None else None,
            'bbox': self.spatial_bounds.to_api_dict() if self.spatial_bounds is not None else None,
            'resolution': self.spatial_resolution.to_api_dict() if self.spatial_resolution is not None else None,
        })


class VectorDataType(str, Enum):
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

    def to_api_enum(self) -> api.VectorDataType:
        return api.VectorDataType(self.value)

    @staticmethod
    def from_literal(literal: Literal['Data', 'MultiPoint', 'MultiLineString', 'MultiPolygon']) -> VectorDataType:
        '''Resolve vector data type from literal'''
        return VectorDataType(literal)

    @staticmethod
    def from_api_enum(data_type: api.VectorDataType) -> VectorDataType:
        '''Resolve vector data type from API enum'''
        return VectorDataType(data_type.value)

    @staticmethod
    def from_string(string: str) -> VectorDataType:
        '''Resolve vector data type from string'''
        if string not in VectorDataType.__members__.values():
            raise InputException("Invalid vector data type: " + string)
        return VectorDataType(string)


class TimeStepGranularity(Enum):
    '''An enum of time step granularities'''
    MILLIS = 'Millis'
    SECONDS = 'Seconds'
    MINUTES = 'Minutes'
    HOURS = 'Hours'
    DAYS = 'Days'
    MONTHS = 'Months'
    YEARS = 'Years'

    def to_api_enum(self) -> api.TimeStepGranularity:
        return api.TimeStepGranularity(self.value)


@dataclass
class TimeStep:
    '''A time step that consists of a granularity and a step size'''
    step: int
    granularity: TimeStepGranularity

    def to_api_dict(self) -> api.TimeStep:
        return api.TimeStep({
            'step': self.step,
            'granularity': self.granularity.to_api_enum(),
        })


@dataclass
class Provenance:
    '''Provenance information as triplet of citation, license and uri'''

    citation: str
    license: str
    uri: str

    @classmethod
    def from_response(cls, response: api.Provenance) -> Provenance:
        '''Parse an http response to a `Provenance` object'''
        return Provenance(response['citation'], response['license'], response['uri'])

    def to_api_dict(self) -> api.Provenance:
        return api.Provenance({
            'citation': self.citation,
            'license': self.license,
            'uri': self.uri,
        })


@dataclass
class ProvenanceEntry:
    '''Provenance of a dataset'''

    data: List[DataId]
    provenance: Provenance

    @classmethod
    def from_response(cls, response: api.ProvenanceEntry) -> ProvenanceEntry:
        '''Parse an http response to a `ProvenanceEntry` object'''

        dataset = [DataId.from_response(data) for data in response['data']]
        provenance = Provenance.from_response(response['provenance'])

        return ProvenanceEntry(dataset, provenance)


class Symbology:
    '''Base class for symbology'''

    @abstractmethod
    def to_api_dict(self) -> api.Symbology:
        pass

    @staticmethod
    def from_response(response: api.Symbology) -> Symbology:
        '''Parse an http response to a `Symbology` object'''

        if response['type'] == 'vector':
            # return VectorSymbology.from_response_vector(response)
            return VectorSymbology()  # TODO: implement
        if response['type'] == 'raster':
            return RasterSymbology.from_response_raster(cast(api.RasterSymbology, response))

        raise InputException("Invalid symbology type")


class VectorSymbology(Symbology):
    '''A vector symbology'''

    # TODO: implement

    def to_api_dict(self) -> api.Symbology:
        return api.Symbology({
            'type': 'vector',
        })


class RasterSymbology(Symbology):
    '''A raster symbology'''
    __opacity: float
    __colorizer: Colorizer

    def __init__(self, colorizer: Colorizer, opacity: float = 1.0) -> None:
        '''Initialize a new `RasterSymbology`'''

        self.__colorizer = colorizer
        self.__opacity = opacity

    def to_api_dict(self) -> api.RasterSymbology:
        '''Convert the raster symbology to a dictionary'''

        return api.RasterSymbology({
            'type': 'raster',
            'colorizer': self.__colorizer.to_api_dict(),
            'opacity': self.__opacity,
        })

    @staticmethod
    def from_response_raster(response: api.RasterSymbology) -> RasterSymbology:
        '''Parse an http response to a `RasterSymbology` object'''

        colorizer = Colorizer.from_response(response['colorizer'])

        return RasterSymbology(colorizer, response['opacity'])

    def __repr__(self) -> str:
        return super().__repr__() + f"({self.__colorizer}, {self.__opacity})"


class DataId:  # pylint: disable=too-few-public-methods
    '''Base class for data ids'''
    @classmethod
    def from_response(cls, response: api.DataId) -> DataId:
        '''Parse an http response to a `DataId` object'''

        if response["type"] == "internal":
            return InternalDataId.from_response_internal(cast(api.InternalDataId, response))
        if response["type"] == "external":
            return ExternalDataId.from_response_external(cast(api.ExternalDataId, response))

        raise GeoEngineException({"message": f"Unknown DataId type: {response['type']}"})

    @abstractmethod
    def to_api_dict(self) -> api.DataId:
        pass


class InternalDataId(DataId):
    '''An internal data id'''

    __dataset_id: UUID

    def __init__(self, dataset_id: UUID):
        self.__dataset_id = dataset_id

    @classmethod
    def from_response_internal(cls, response: api.InternalDataId) -> InternalDataId:
        '''Parse an http response to a `InternalDataId` object'''
        return InternalDataId(UUID(response['datasetId']))

    def to_api_dict(self) -> api.InternalDataId:
        return api.InternalDataId({
            "type": "internal",
            "datasetId": str(self.__dataset_id)
        })

    def __str__(self) -> str:
        return str(self.__dataset_id)

    def __repr__(self) -> str:
        '''Display representation of an internal data id'''
        return str(self)

    def __eq__(self, other) -> bool:
        '''Check if two internal data ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__dataset_id == other.__dataset_id  # pylint: disable=protected-access


class ExternalDataId(DataId):
    '''An external data id'''

    __provider_id: UUID
    __layer_id: str

    def __init__(self, provider_id: UUID, layer_id: str):
        self.__provider_id = provider_id
        self.__layer_id = layer_id

    @classmethod
    def from_response_external(cls, response: api.ExternalDataId) -> ExternalDataId:
        '''Parse an http response to a `ExternalDataId` object'''

        return ExternalDataId(UUID(response['providerId']), response['layerId'])

    def to_api_dict(self) -> api.ExternalDataId:
        return api.ExternalDataId({
            "type": "external",
            "providerId": str(self.__provider_id),
            "layerId": self.__layer_id,
        })

    def __str__(self) -> str:
        return f'{self.__provider_id}:{self.__layer_id}'

    def __repr__(self) -> str:
        '''Display representation of an external data id'''
        return str(self)

    def __eq__(self, other) -> bool:
        '''Check if two external data ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__provider_id == other.__provider_id and self.__layer_id == other.__layer_id  # pylint: disable=protected-access


class Measurement:  # pylint: disable=too-few-public-methods
    '''
    Base class for measurements
    '''

    @staticmethod
    def from_response(response: api.Measurement) -> Measurement:
        '''
        Parse a result descriptor from an http response
        '''

        if 'error' in response:
            raise GeoEngineException(cast(api.GeoEngineExceptionResponse, response))

        measurement_type = response['type']

        if measurement_type == 'unitless':
            return UnitlessMeasurement()
        if measurement_type == 'continuous':
            return ContinuousMeasurement.from_response_continuous(cast(api.ContinuousMeasurement, response))
        if measurement_type == 'classification':
            return ClassificationMeasurement.from_response_classification(cast(api.ClassificationMeasurement, response))

        raise TypeException(
            f'Unknown `Measurement` type: {measurement_type}')

    @abstractmethod
    def to_api_dict(self) -> api.Measurement:
        pass


class UnitlessMeasurement(Measurement):
    '''A measurement that is unitless'''

    def __str__(self) -> str:
        '''String representation of a unitless measurement'''
        return 'unitless'

    def __repr__(self) -> str:
        '''Display representation of a unitless measurement'''
        return str(self)

    def to_api_dict(self) -> api.Measurement:
        return api.Measurement({
            'type': 'unitless'
        })


class ContinuousMeasurement(Measurement):
    '''A measurement that is continuous'''

    __measurement: str
    __unit: Optional[str]

    def __init__(self, measurement: str, unit: Optional[str]) -> None:
        '''Initialize a new `ContiuousMeasurement`'''

        super().__init__()

        self.__measurement = measurement
        self.__unit = unit

    @staticmethod
    def from_response_continuous(response: api.ContinuousMeasurement) -> ContinuousMeasurement:
        '''Initialize a new `ContiuousMeasurement from a JSON response'''

        return ContinuousMeasurement(response['measurement'], response.get('unit', None))

    def __str__(self) -> str:
        '''String representation of a continuous measurement'''

        if self.__unit is None:
            return self.__measurement

        return f'{self.__measurement} ({self.__unit})'

    def __repr__(self) -> str:
        '''Display representation of a continuous measurement'''
        return str(self)

    def to_api_dict(self) -> api.ContinuousMeasurement:
        return api.ContinuousMeasurement({
            'type': 'continuous',
            'measurement': self.__measurement,
            'unit': self.__unit
        })

    @property
    def measurement(self) -> str:
        return self.__measurement

    @property
    def unit(self) -> Optional[str]:
        return self.__unit


class ClassificationMeasurement(Measurement):
    '''A measurement that is a classification'''

    __measurement: str
    __classes: Dict[int, str]

    def __init__(self, measurement: str, classes: Dict[int, str]) -> None:
        '''Initialize a new `ClassificationMeasurement`'''

        super().__init__()

        self.__measurement = measurement
        self.__classes = classes

    @staticmethod
    def from_response_classification(response: api.ClassificationMeasurement) -> ClassificationMeasurement:
        '''Initialize a new `ClassificationMeasurement from a JSON response'''

        measurement = response['measurement']

        str_classes: Dict[str, str] = response['classes']
        classes = {int(k): v for k, v in str_classes.items()}

        return ClassificationMeasurement(measurement, classes)

    def to_api_dict(self) -> api.ClassificationMeasurement:
        str_classes: Dict[str, str] = {str(k): v for k, v in self.__classes.items()}

        return api.ClassificationMeasurement({
            'type': 'classification',
            'measurement': self.__measurement,
            'classes': str_classes
        })

    def __str__(self) -> str:
        '''String representation of a classification measurement'''
        classes_str = ', '.join(f'{k}: {v}' for k, v in self.__classes.items())
        return f'{self.__measurement} ({classes_str})'

    def __repr__(self) -> str:
        '''Display representation of a classification measurement'''
        return str(self)

    @property
    def measurement(self) -> str:
        return self.__measurement

    @property
    def classes(self) -> Dict[int, str]:
        return self.__classes
