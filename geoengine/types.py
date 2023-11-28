# pylint: disable=too-many-lines

'''
Different type mappings of geo engine types
'''

from __future__ import annotations
from abc import abstractmethod
from datetime import datetime, timezone
from uuid import UUID
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union, cast, List, Literal
from attr import dataclass
import numpy as np
import geoengine_openapi_client
from geoengine.colorizer import Colorizer
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

    def to_api_dict(self) -> geoengine_openapi_client.BoundingBox2D:
        return geoengine_openapi_client.BoundingBox2D(
            lower_left_coordinate=geoengine_openapi_client.Coordinate2D(
                x=self.xmin,
                y=self.ymin,
            ),
            upper_right_coordinate=geoengine_openapi_client.Coordinate2D(
                x=self.xmax,
                y=self.ymax,
            ),
        )

    @staticmethod
    def from_response(response: geoengine_openapi_client.BoundingBox2D) -> BoundingBox2D:
        '''create a `BoundingBox2D` from an API response'''
        lower_left = response.lower_left_coordinate
        upper_right = response.upper_right_coordinate

        return BoundingBox2D(
            lower_left.x,
            lower_left.y,
            upper_right.x,
            upper_right.y,
        )

    def __repr__(self) -> str:
        return f'BoundingBox2D(xmin={self.xmin}, ymin={self.ymin}, xmax={self.xmax}, ymax={self.ymax})'


class SpatialPartition2D(SpatialBounds):
    '''A 2D spatial partition.'''

    @staticmethod
    def from_response(response: geoengine_openapi_client.SpatialPartition2D) -> SpatialPartition2D:
        '''create a `SpatialPartition2D` from an API response'''
        upper_left = response.upper_left_coordinate
        lower_right = response.lower_right_coordinate

        return SpatialPartition2D(
            upper_left.x,
            lower_right.y,
            lower_right.x,
            upper_left.y,

        )

    def to_api_dict(self) -> geoengine_openapi_client.SpatialPartition2D:
        return geoengine_openapi_client.SpatialPartition2D(
            upper_left_coordinate=geoengine_openapi_client.Coordinate2D(
                x=self.xmin,
                y=self.ymax,
            ),
            lower_right_coordinate=geoengine_openapi_client.Coordinate2D(
                x=self.xmax,
                y=self.ymin,
            ),
        )

    def to_bounding_box(self) -> BoundingBox2D:
        '''convert to a `BoundingBox2D`'''
        return BoundingBox2D(self.xmin, self.ymin, self.xmax, self.ymax)


class TimeInterval:
    ''''A time interval.'''
    start: np.datetime64
    end: Optional[np.datetime64]

    def __init__(self,
                 start: Union[datetime, np.datetime64],
                 end: Optional[Union[datetime, np.datetime64]] = None) -> None:
        '''Initialize a new `TimeInterval` object'''

        if isinstance(start, np.datetime64):
            self.start = start
        elif isinstance(start, datetime):
            # We assume that a datetime without a timezone means UTC
            if start.tzinfo is not None:
                start = start.astimezone(tz=timezone.utc).replace(tzinfo=None)
            self.start = np.datetime64(start)
        else:
            raise InputException("`start` must be of type `datetime.datetime` or `numpy.datetime64`")

        if end is None:
            self.end = None
        elif isinstance(end, np.datetime64):
            self.end = end
        elif isinstance(end, datetime):
            # We assume that a datetime without a timezone means UTC
            if end.tzinfo is not None:
                end = end.astimezone(tz=timezone.utc).replace(tzinfo=None)
            self.end = np.datetime64(end)
        else:
            raise InputException("`end` must be of type `datetime.datetime` or `numpy.datetime64`")

        # Check validity of time interval if an `end` exists
        if end is not None and start > end:
            raise InputException("Time inverval: Start must be <= End")

    def is_instant(self) -> bool:
        return self.end is None

    @property
    def time_str(self) -> str:
        '''
        Return the time instance or interval as a string representation
        '''

        start_iso = TimeInterval.__datetime_to_iso_str(self.start)

        if self.end is None or self.start == self.end:
            return start_iso

        end_iso = TimeInterval.__datetime_to_iso_str(self.end)

        return start_iso + '/' + end_iso

    @staticmethod
    def from_response(response: Any) -> TimeInterval:
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

    def to_api_dict(self) -> geoengine_openapi_client.TimeInterval:
        '''Convert the time interval to a dictionary'''

        start = int(self.start.astype('datetime64[ms]').astype(int))
        end = int(self.end.astype('datetime64[ms]').astype(int)) if self.end is not None else start
        return geoengine_openapi_client.TimeInterval(
            start=start,
            end=end,
        )

    @staticmethod
    def __datetime_to_iso_str(timestamp: np.datetime64) -> str:
        return str(np.datetime_as_string(timestamp, unit='ms', timezone='UTC')).replace('Z', '+00:00')


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

    def to_api_dict(self) -> geoengine_openapi_client.SpatialResolution:
        return geoengine_openapi_client.SpatialResolution(
            x=self.x_resolution,
            y=self.y_resolution,
        )

    @staticmethod
    def from_response(response: geoengine_openapi_client.SpatialResolution) -> SpatialResolution:
        '''create a `SpatialResolution` from an API response'''
        return SpatialResolution(x_resolution=response.x, y_resolution=response.y)

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
                 spatial_bounds: Union[BoundingBox2D, Tuple[float, float, float, float]],
                 time_interval: Union[TimeInterval, Tuple[datetime, Optional[datetime]]],
                 resolution: Union[SpatialResolution, Tuple[float, float]],
                 srs='EPSG:4326') -> None:
        """
        Initialize a new `QueryRectangle` object

        Parameters
        ----------
        spatial_bounds
            The spatial bounds of the query rectangle.
            Either a `BoundingBox2D` or a tuple of floats (xmin, ymin, xmax, ymax)
        time_interval
            The time interval of the query rectangle.
            Either a `TimeInterval` or a tuple of `datetime.datetime` objects (start, end)
        resolution
            The spatial resolution of the query rectangle.
            Either a `SpatialResolution` or a tuple of floats (x_resolution, y_resolution)
        """

        if not isinstance(spatial_bounds, BoundingBox2D):
            spatial_bounds = BoundingBox2D(*spatial_bounds)
        if not isinstance(time_interval, TimeInterval):
            time_interval = TimeInterval(*time_interval)
        if not isinstance(resolution, SpatialResolution):
            resolution = SpatialResolution(*resolution)

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

    def as_raster_query_rectangle_api_dict(self) -> geoengine_openapi_client.RasterQueryRectangle:
        '''Return the query rectangle as a dictionary for the API'''
        return geoengine_openapi_client.RasterQueryRectangle(
            spatial_bounds=SpatialPartition2D(
                self.spatial_bounds.xmin,
                self.spatial_bounds.ymin,
                self.spatial_bounds.xmax,
                self.spatial_bounds.ymax,
            ).to_api_dict(),
            spatial_resolution=self.spatial_resolution.to_api_dict(),
            time_interval=self.time.to_api_dict(),
        )


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
    def from_response(response: geoengine_openapi_client.TypedResultDescriptor) -> ResultDescriptor:
        '''
        Parse a result descriptor from an http response
        '''

        inner = response.actual_instance

        if isinstance(inner, geoengine_openapi_client.RasterResultDescriptorWithType):
            return RasterResultDescriptor.from_response_raster(inner)
        if isinstance(inner, geoengine_openapi_client.VectorResultDescriptorWithType):
            return VectorResultDescriptor.from_response_vector(inner)
        if isinstance(inner, geoengine_openapi_client.PlotResultDescriptorWithType):
            return PlotResultDescriptor.from_response_plot(inner)

        raise TypeException(f'Unknown `ResultDescriptor` type: {inner.type}')

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
    def to_api_dict(self) -> geoengine_openapi_client.TypedResultDescriptor:
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
        spatial_bounds: Optional[BoundingBox2D] = None
    ) -> None:
        ''' Initialize a vector result descriptor '''
        super().__init__(spatial_reference, time_bounds, None)
        self.__data_type = data_type
        self.__columns = columns
        self.__spatial_bounds = spatial_bounds

    @staticmethod
    def from_response_vector(
            response: geoengine_openapi_client.VectorResultDescriptorWithType) -> VectorResultDescriptor:
        '''Parse a vector result descriptor from an http response'''
        sref = response.spatial_reference
        data_type = VectorDataType.from_string(response.data_type)
        columns = {name: VectorColumnInfo.from_response(info) for name, info in response.columns.items()}

        time_bounds = None
        # FIXME: datetime can not represent our min max range
        # if 'time' in response and response['time'] is not None:
        #    time_bounds = TimeInterval.from_response(response['time'])
        spatial_bounds = None
        if response.bbox is not None:
            spatial_bounds = BoundingBox2D.from_response(response.bbox)

        return VectorResultDescriptor(sref, data_type, columns, time_bounds, spatial_bounds)

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
        r += f'Data type:         {self.data_type.value}\n'
        r += f'Spatial Reference: {self.spatial_reference}\n'

        r += 'Columns:\n'
        for column_name in self.columns:
            column_info = self.columns[column_name]
            r += f'  {column_name}:\n'
            r += f'    Column Type: {column_info.data_type.value}\n'
            r += f'    Measurement: {column_info.measurement}\n'

        return r

    def to_api_dict(self) -> geoengine_openapi_client.TypedResultDescriptor:
        '''Convert the vector result descriptor to a dictionary'''

        return geoengine_openapi_client.TypedResultDescriptor(geoengine_openapi_client.VectorResultDescriptorWithType(
            type='vector',
            data_type=self.data_type.to_api_enum(),
            spatial_reference=self.spatial_reference,
            columns={name: column_info.to_api_dict() for name, column_info in self.columns.items()},
            time=self.time_bounds.time_str if self.time_bounds is not None else None,
            bbox=self.spatial_bounds.to_api_dict() if self.spatial_bounds is not None else None,
            resolution=self.spatial_resolution.to_api_dict() if self.spatial_resolution is not None else None,
        ))


class FeatureDataType(str, Enum):
    '''Vector column data type'''

    CATEGORY = "category"
    INT = "int"
    FLOAT = "float"
    TEXT = "text"
    BOOL = "bool"
    DATETIME = "dateTime"

    @staticmethod
    def from_string(data_type: str) -> FeatureDataType:
        '''Create a new `VectorColumnDataType` from a string'''

        return FeatureDataType(data_type)

    def to_api_enum(self) -> geoengine_openapi_client.FeatureDataType:
        '''Convert to an API enum'''

        return geoengine_openapi_client.FeatureDataType(self.value)


@dataclass
class VectorColumnInfo:
    '''Vector column information'''

    data_type: FeatureDataType
    measurement: Measurement

    @staticmethod
    def from_response(response: geoengine_openapi_client.VectorColumnInfo) -> VectorColumnInfo:
        '''Create a new `VectorColumnInfo` from a JSON response'''

        return VectorColumnInfo(
            FeatureDataType.from_string(response.data_type),
            Measurement.from_response(response.measurement)
        )

    def to_api_dict(self) -> geoengine_openapi_client.VectorColumnInfo:
        '''Convert to a dictionary'''

        return geoengine_openapi_client.VectorColumnInfo(
            data_type=self.data_type.to_api_enum(),
            measurement=self.measurement.to_api_dict(),
        )


@dataclass(repr=False)
class RasterBandDescriptor:
    '''A raster band descriptor'''

    name: str
    measurement: Measurement

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.RasterBandDescriptor) -> RasterBandDescriptor:
        '''Parse an http response to a `Provenance` object'''
        return RasterBandDescriptor(response.name, Measurement.from_response(response.measurement))

    def to_api_dict(self) -> geoengine_openapi_client.RasterBandDescriptor:
        return geoengine_openapi_client.RasterBandDescriptor(
            name=self.name,
            measurement=self.measurement.to_api_dict(),
        )

    def __repr__(self) -> str:
        '''Display representation of a raster band descriptor'''
        return f'{self.name}: {self.measurement}'


class RasterResultDescriptor(ResultDescriptor):
    '''
    A raster result descriptor
    '''
    __data_type: Literal['U8', 'U16', 'U32', 'U64', 'I8', 'I16', 'I32', 'I64', 'F32', 'F64']
    __bands: List[RasterBandDescriptor]
    __spatial_bounds: Optional[SpatialPartition2D]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        data_type: Literal['U8', 'U16', 'U32', 'U64', 'I8', 'I16', 'I32', 'I64', 'F32', 'F64'],
        bands: List[RasterBandDescriptor],
        spatial_reference: str,
        time_bounds: Optional[TimeInterval] = None,
        spatial_bounds: Optional[SpatialPartition2D] = None,
        spatial_resolution: Optional[SpatialResolution] = None
    ) -> None:
        '''Initialize a new `RasterResultDescriptor`'''
        super().__init__(spatial_reference, time_bounds, spatial_resolution)
        self.__data_type = data_type
        self.__bands = bands
        self.__spatial_bounds = spatial_bounds

    def to_api_dict(self) -> geoengine_openapi_client.TypedResultDescriptor:
        '''Convert the raster result descriptor to a dictionary'''

        return geoengine_openapi_client.TypedResultDescriptor(geoengine_openapi_client.RasterResultDescriptorWithType(
            type='raster',
            data_type=self.data_type,
            bands=[band.to_api_dict() for band in self.__bands],
            spatial_reference=self.spatial_reference,
            time=self.time_bounds.to_api_dict() if self.time_bounds is not None else None,
            bbox=self.spatial_bounds.to_api_dict() if self.spatial_bounds is not None else None,
            resolution=self.spatial_resolution.to_api_dict() if self.spatial_resolution is not None else None
        ))

    @staticmethod
    def from_response_raster(
            response: geoengine_openapi_client.RasterResultDescriptorWithType) -> RasterResultDescriptor:
        '''Parse a raster result descriptor from an http response'''
        spatial_ref = response.spatial_reference
        data_type = response.data_type.value
        bands = [RasterBandDescriptor.from_response(band) for band in response.bands]

        time_bounds = None
        # FIXME: datetime can not represent our min max range
        # if 'time' in response and response['time'] is not None:
        #    time_bounds = TimeInterval.from_response(response['time'])
        spatial_bounds = None
        if response.bbox is not None:
            spatial_bounds = SpatialPartition2D.from_response(response.bbox)
        spatial_resolution = None
        if response.resolution is not None:
            spatial_resolution = SpatialResolution.from_response(response.resolution)

        return RasterResultDescriptor(
            data_type=data_type,
            bands=bands,
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
    def bands(self) -> List[RasterBandDescriptor]:
        return self.__bands

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
        r += 'Bands:\n'

        for band in self.__bands:
            r += f'    {band}\n'

        return r


class PlotResultDescriptor(ResultDescriptor):
    '''
    A plot result descriptor
    '''

    __spatial_bounds: Optional[BoundingBox2D]

    def __init__(  # pylint: disable=too-many-arguments]
        self,
        spatial_reference: str,
        time_bounds: Optional[TimeInterval] = None,
        spatial_bounds: Optional[BoundingBox2D] = None
    ) -> None:
        '''Initialize a new `PlotResultDescriptor`'''
        super().__init__(spatial_reference, time_bounds, None)
        self.__spatial_bounds = spatial_bounds

    def __repr__(self) -> str:
        '''Display representation of the plot result descriptor'''
        r = 'Plot Result'

        return r

    @staticmethod
    def from_response_plot(response: geoengine_openapi_client.PlotResultDescriptorWithType) -> PlotResultDescriptor:
        '''Create a new `PlotResultDescriptor` from a JSON response'''
        spatial_ref = response.spatial_reference

        time_bounds = None
        # FIXME: datetime can not represent our min max range
        # if 'time' in response and response['time'] is not None:
        #    time_bounds = TimeInterval.from_response(response['time'])
        spatial_bounds = None
        if response.bbox is not None:
            spatial_bounds = BoundingBox2D.from_response(response.bbox)

        return PlotResultDescriptor(
            spatial_reference=spatial_ref,
            time_bounds=time_bounds,
            spatial_bounds=spatial_bounds
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

    def to_api_dict(self) -> geoengine_openapi_client.TypedResultDescriptor:
        '''Convert the plot result descriptor to a dictionary'''

        return geoengine_openapi_client.TypedResultDescriptor(geoengine_openapi_client.PlotResultDescriptorWithType(
            type='plot',
            spatial_reference=self.spatial_reference,
            data_type='Plot',
            time=self.time_bounds.time_str if self.time_bounds is not None else None,
            bbox=self.spatial_bounds.to_api_dict() if self.spatial_bounds is not None else None
        ))


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

    def to_api_enum(self) -> geoengine_openapi_client.VectorDataType:
        return geoengine_openapi_client.VectorDataType(self.value)

    @staticmethod
    def from_literal(literal: Literal['Data', 'MultiPoint', 'MultiLineString', 'MultiPolygon']) -> VectorDataType:
        '''Resolve vector data type from literal'''
        return VectorDataType(literal)

    @staticmethod
    def from_api_enum(data_type: geoengine_openapi_client.VectorDataType) -> VectorDataType:
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
    MILLIS = 'millis'
    SECONDS = 'seconds'
    MINUTES = 'minutes'
    HOURS = 'hours'
    DAYS = 'days'
    MONTHS = 'months'
    YEARS = 'years'

    def to_api_enum(self) -> geoengine_openapi_client.TimeGranularity:
        return geoengine_openapi_client.TimeGranularity(self.value)


@dataclass
class TimeStep:
    '''A time step that consists of a granularity and a step size'''
    step: int
    granularity: TimeStepGranularity

    def to_api_dict(self) -> geoengine_openapi_client.TimeStep:
        return geoengine_openapi_client.TimeStep(
            step=self.step,
            granularity=self.granularity.to_api_enum(),
        )


@dataclass
class Provenance:
    '''Provenance information as triplet of citation, license and uri'''

    citation: str
    license: str
    uri: str

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.Provenance) -> Provenance:
        '''Parse an http response to a `Provenance` object'''
        return Provenance(response.citation, response.license, response.uri)

    def to_api_dict(self) -> geoengine_openapi_client.Provenance:
        return geoengine_openapi_client.Provenance(
            citation=self.citation,
            license=self.license,
            uri=self.uri,
        )


@dataclass
class ProvenanceEntry:
    '''Provenance of a dataset'''

    data: List[DataId]
    provenance: Provenance

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.ProvenanceEntry) -> ProvenanceEntry:
        '''Parse an http response to a `ProvenanceEntry` object'''

        dataset = [DataId.from_response(data) for data in response.data]
        provenance = Provenance.from_response(response.provenance)

        return ProvenanceEntry(dataset, provenance)


class Symbology:
    '''Base class for symbology'''

    @abstractmethod
    def to_api_dict(self) -> geoengine_openapi_client.Symbology:
        pass

    @staticmethod
    def from_response(response: geoengine_openapi_client.Symbology) -> Symbology:
        '''Parse an http response to a `Symbology` object'''
        inner = response.actual_instance

        if isinstance(inner, (
                geoengine_openapi_client.PointSymbologyWithType,
                geoengine_openapi_client.LineSymbologyWithType,
                geoengine_openapi_client.PolygonSymbologyWithType)):
            # return VectorSymbology.from_response_vector(response)
            return VectorSymbology()  # TODO: implement
        if isinstance(inner, geoengine_openapi_client.RasterSymbologyWithType):
            return RasterSymbology.from_response_raster(inner)

        raise InputException("Invalid symbology type")


class VectorSymbology(Symbology):
    '''A vector symbology'''

    # TODO: implement

    def to_api_dict(self) -> geoengine_openapi_client.Symbology:
        return None  # type: ignore


class RasterSymbology(Symbology):
    '''A raster symbology'''
    __opacity: float
    __colorizer: Colorizer

    def __init__(self, colorizer: Colorizer, opacity: float = 1.0) -> None:
        '''Initialize a new `RasterSymbology`'''

        self.__colorizer = colorizer
        self.__opacity = opacity

    def to_api_dict(self) -> geoengine_openapi_client.Symbology:
        '''Convert the raster symbology to a dictionary'''

        return geoengine_openapi_client.Symbology(geoengine_openapi_client.RasterSymbologyWithType(
            type='raster',
            colorizer=self.__colorizer.to_api_dict(),
            opacity=self.__opacity,
        ))

    @staticmethod
    def from_response_raster(response: geoengine_openapi_client.RasterSymbologyWithType) -> RasterSymbology:
        '''Parse an http response to a `RasterSymbology` object'''

        colorizer = Colorizer.from_response(response.colorizer)

        return RasterSymbology(colorizer, response.opacity)

    def __repr__(self) -> str:
        return super().__repr__() + f"({self.__colorizer}, {self.__opacity})"


class DataId:  # pylint: disable=too-few-public-methods
    '''Base class for data ids'''
    @classmethod
    def from_response(cls, response: geoengine_openapi_client.DataId) -> DataId:
        '''Parse an http response to a `DataId` object'''
        inner = response.actual_instance

        if isinstance(inner, geoengine_openapi_client.InternalDataId):
            return InternalDataId.from_response_internal(inner)
        if isinstance(inner, geoengine_openapi_client.ExternalDataIdWithType):
            return ExternalDataId.from_response_external(inner)

        raise GeoEngineException({"message": f"Unknown DataId type: {inner.type}"})

    @abstractmethod
    def to_api_dict(self) -> geoengine_openapi_client.DataId:
        pass


class InternalDataId(DataId):
    '''An internal data id'''

    __dataset_id: UUID

    def __init__(self, dataset_id: UUID):
        self.__dataset_id = dataset_id

    @classmethod
    def from_response_internal(cls, response: geoengine_openapi_client.InternalDataId) -> InternalDataId:
        '''Parse an http response to a `InternalDataId` object'''
        return InternalDataId(UUID(response.dataset_id))

    def to_api_dict(self) -> geoengine_openapi_client.DataId:
        return geoengine_openapi_client.DataId(geoengine_openapi_client.InternalDataId(
            type="internal",
            dataset_id=str(self.__dataset_id)
        ))

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
    def from_response_external(cls, response: geoengine_openapi_client.ExternalDataIdWithType) -> ExternalDataId:
        '''Parse an http response to a `ExternalDataId` object'''

        return ExternalDataId(UUID(response.provider_id), response.layer_id)

    def to_api_dict(self) -> geoengine_openapi_client.DataId:
        return geoengine_openapi_client.DataId(geoengine_openapi_client.ExternalDataIdWithType(
            type="external",
            provider_id=str(self.__provider_id),
            layer_id=self.__layer_id,
        ))

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
    def from_response(response: geoengine_openapi_client.Measurement) -> Measurement:
        '''
        Parse a result descriptor from an http response
        '''
        inner = response.actual_instance

        if isinstance(inner, geoengine_openapi_client.UnitlessMeasurement):
            return UnitlessMeasurement()
        if isinstance(inner, geoengine_openapi_client.ContinuousMeasurementWithType):
            return ContinuousMeasurement.from_response_continuous(inner)
        if isinstance(inner, geoengine_openapi_client.ClassificationMeasurementWithType):
            return ClassificationMeasurement.from_response_classification(inner)

        raise TypeException(
            f'Unknown `Measurement` type: {inner.type}')

    @abstractmethod
    def to_api_dict(self) -> geoengine_openapi_client.Measurement:
        pass


class UnitlessMeasurement(Measurement):
    '''A measurement that is unitless'''

    def __str__(self) -> str:
        '''String representation of a unitless measurement'''
        return 'unitless'

    def __repr__(self) -> str:
        '''Display representation of a unitless measurement'''
        return str(self)

    def to_api_dict(self) -> geoengine_openapi_client.Measurement:
        return geoengine_openapi_client.Measurement(geoengine_openapi_client.UnitlessMeasurement(
            type='unitless'
        ))


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
    def from_response_continuous(
            response: geoengine_openapi_client.ContinuousMeasurementWithType) -> ContinuousMeasurement:
        '''Initialize a new `ContiuousMeasurement from a JSON response'''

        return ContinuousMeasurement(response.measurement, response.unit)

    def __str__(self) -> str:
        '''String representation of a continuous measurement'''

        if self.__unit is None:
            return self.__measurement

        return f'{self.__measurement} ({self.__unit})'

    def __repr__(self) -> str:
        '''Display representation of a continuous measurement'''
        return str(self)

    def to_api_dict(self) -> geoengine_openapi_client.Measurement:
        return geoengine_openapi_client.Measurement(geoengine_openapi_client.ContinuousMeasurementWithType(
            type='continuous',
            measurement=self.__measurement,
            unit=self.__unit
        ))

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
    def from_response_classification(
        response: geoengine_openapi_client.ClassificationMeasurementWithType
    ) -> ClassificationMeasurement:
        '''Initialize a new `ClassificationMeasurement from a JSON response'''

        measurement = response.measurement

        str_classes: Dict[str, str] = response.classes
        classes = {int(k): v for k, v in str_classes.items()}

        return ClassificationMeasurement(measurement, classes)

    def to_api_dict(self) -> geoengine_openapi_client.Measurement:
        str_classes: Dict[str, str] = {str(k): v for k, v in self.__classes.items()}

        return geoengine_openapi_client.Measurement(geoengine_openapi_client.ClassificationMeasurementWithType(
            type='classification',
            measurement=self.__measurement,
            classes=str_classes
        ))

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


class GeoTransform:
    '''The `GeoTransform` specifies the relationship between pixel coordinates and geographic coordinates.'''

    x_min: float
    y_max: float
    '''In Geo Engine, x_pixel_size is always positive.'''
    x_pixel_size: float
    '''In Geo Engine, y_pixel_size is always negative.'''
    y_pixel_size: float

    def __init__(self, x_min: float, y_max: float, x_pixel_size: float, y_pixel_size: float):
        '''Initialize a new `GeoTransform`'''

        assert x_pixel_size > 0, 'In Geo Engine, x_pixel_size is always positive.'
        assert y_pixel_size < 0, 'In Geo Engine, y_pixel_size is always negative.'

        self.x_min = x_min
        self.y_max = y_max
        self.x_pixel_size = x_pixel_size
        self.y_pixel_size = y_pixel_size

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.GdalDatasetGeoTransform) -> GeoTransform:
        '''Parse a geotransform from an HTTP JSON response'''

        return GeoTransform(
            x_min=response.origin_coordinate.x,
            y_max=response.origin_coordinate.y,
            x_pixel_size=response.x_pixel_size,
            y_pixel_size=response.y_pixel_size,
        )

    def to_api_dict(self) -> geoengine_openapi_client.GdalDatasetGeoTransform:
        return geoengine_openapi_client.GdalDatasetGeoTransform(
            origin_coordinate=geoengine_openapi_client.Coordinate2D(
                x=self.x_min,
                y=self.y_max,
            ),
            x_pixel_size=self.x_pixel_size,
            y_pixel_size=self.y_pixel_size
        )

    def to_gdal(self) -> Tuple[float, float, float, float, float, float]:
        '''Convert to a GDAL geotransform'''
        return (self.x_min, self.x_pixel_size, 0, self.y_max, 0, self.y_pixel_size)

    def __str__(self) -> str:
        return f'Origin: ({self.x_min}, {self.y_max}), ' \
            f'X Pixel Size: {self.x_pixel_size}, ' \
            f'Y Pixel Size: {self.y_pixel_size}'

    def __repr__(self) -> str:
        return str(self)

    @property
    def x_half_pixel_size(self) -> float:
        return self.x_pixel_size / 2.0

    @property
    def y_half_pixel_size(self) -> float:
        return self.y_pixel_size / 2.0

    def x_max(self, number_of_pixels: int) -> float:
        return self.x_min + number_of_pixels * self.x_pixel_size

    def y_min(self, number_of_pixels: int) -> float:
        return self.y_max + number_of_pixels * self.y_pixel_size

    def coord_to_pixel_ul(self, x_cord: float, y_coord: float) -> Tuple[int, int]:
        '''Convert a coordinate to a pixel index rould towards top left'''
        return (int(np.floor((x_cord - self.x_min) / self.x_pixel_size)),
                int(np.ceil((y_coord - self.y_max) / self.y_pixel_size)))

    def coord_to_pixel_lr(self, x_cord: float, y_coord: float) -> Tuple[int, int]:
        '''Convert a coordinate to a pixel index ound towards lower right'''
        return (int(np.ceil((x_cord - self.x_min) / self.x_pixel_size)),
                int(np.floor((y_coord - self.y_max) / self.y_pixel_size)))

    def spatial_resolution(self) -> SpatialResolution:
        return SpatialResolution(
            x_resolution=abs(self.x_pixel_size),
            y_resolution=abs(self.y_pixel_size)
        )
