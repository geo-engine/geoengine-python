'''This module contains helpers to create workflow operators for the Geo Engine API.'''

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union, cast
from typing_extensions import Literal

from geoengine.datasets import DatasetName
from geoengine.types import Measurement


class Operator():
    '''Base class for all operators.'''

    @abstractmethod
    def name(self) -> str:
        '''Returns the name of the operator.'''

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        '''Returns a dictionary representation of the operator that can be used to create a JSON request for the API.'''

    @abstractmethod
    def data_type(self) -> Literal['Raster', 'Vector']:
        '''Returns the type of the operator.'''

    def to_workflow_dict(self) -> Dict[str, Any]:
        '''Returns a dictionary representation of a workflow that calls the operator" \
             "that can be used to create a JSON request for the workflow API.'''

        return {
            'type': self.data_type(),
            'operator': self.to_dict(),
        }


class RasterOperator(Operator):
    '''Base class for all raster operators.'''

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    def data_type(self) -> Literal['Raster', 'Vector']:
        return 'Raster'


class VectorOperator(Operator):
    '''Base class for all vector operators.'''

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    def data_type(self) -> Literal['Raster', 'Vector']:
        return 'Vector'


class GdalSource(RasterOperator):
    '''A GDAL source operator.'''
    dataset: str

    def __init__(self, dataset: Union[str, DatasetName]):
        '''Creates a new GDAL source operator.'''
        if isinstance(dataset, DatasetName):
            dataset = str(dataset)
        self.dataset = dataset

    def name(self) -> str:
        return 'GdalSource'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.name(),
            'params': {
                "data": self.dataset
            }
        }


class OgrSource(VectorOperator):
    '''An OGR source operator.'''
    dataset: str
    attribute_projection: Optional[str] = None
    attribute_filters: Optional[str] = None

    def __init__(self, dataset: Union[str, DatasetName]):
        '''Creates a new OGR source operator.'''
        if isinstance(dataset, DatasetName):
            dataset = str(dataset)
        self.dataset = dataset

    def name(self) -> str:
        return 'OgrSource'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.name(),
            'params': {
                "data": self.dataset,
                'attributeProjection': self.attribute_projection,
                'attributeFilters': self.attribute_filters,
            }
        }


class Interpolation(RasterOperator):
    '''An interpolation operator.'''
    source: RasterOperator
    interpolation: Literal["biLinear", "nearestNeighbor"] = "biLinear"
    input_resolution: Optional[float] = None

    def __init__(
        self,
            source_operator: RasterOperator,
            interpolation: Literal["biLinear", "nearestNeighbor"] = "biLinear",
            input_resolution: Optional[float] = None
    ):
        '''Creates a new interpolation operator.'''
        self.source = source_operator
        self.interpolation = interpolation
        self.input_resolution = input_resolution
        if input_resolution is not None:
            raise NotImplementedError("Custom input resolution is not yet implemented")

    def name(self) -> str:
        return 'Interpolation'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "interpolation": self.interpolation,
                "inputResolution": {
                    "type": "source"
                }
            },
            "sources": {
                "raster": self.source.to_dict()
            }
        }


class RasterVectorJoin(VectorOperator):
    '''A RasterVectorJoin operator.'''
    raster_sources: List[RasterOperator]
    vector_source: VectorOperator
    new_column_names: List[str]
    temporal_aggregation: Literal["none", "first", "mean"] = "none"
    temporal_aggregation_ignore_nodata: bool = False
    feature_aggregation: Literal["first", "mean"] = "mean"
    feature_aggregation_ignore_nodata: bool = False

    # pylint: disable=too-many-arguments
    def __init__(self,
                 raster_sources: List[RasterOperator],
                 vector_source: VectorOperator,
                 new_column_names: List[str],
                 temporal_aggregation: Literal["none", "first", "mean"] = "none",
                 temporal_aggregation_ignore_nodata: bool = False,
                 feature_aggregation: Literal["first", "mean"] = "mean",
                 feature_aggregation_ignore_nodata: bool = False,
                 ):
        '''Creates a new RasterVectorJoin operator.'''
        self.raster_source = raster_sources
        self.vector_source = vector_source
        self.new_column_names = new_column_names
        self.temporal_aggregation = temporal_aggregation
        self.temporal_aggregation_ignore_nodata = temporal_aggregation_ignore_nodata
        self.feature_aggregation = feature_aggregation
        self.feature_aggregation_ignore_nodata = feature_aggregation_ignore_nodata
        assert (len(self.raster_source) == len(self.new_column_names))

    def name(self) -> str:
        return 'RasterVectorJoin'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "names": self.new_column_names,
                "temporalAggregation": self.temporal_aggregation,
                "temporalAggregationIgnoreNoData": self.temporal_aggregation_ignore_nodata,
                "featureAggregation": self.feature_aggregation,
                "featureAggregationIgnoreNoData": self.feature_aggregation_ignore_nodata,
            },
            "sources": {
                "vector": self.vector_source.to_dict(),
                "rasters": [raster_source.to_dict() for raster_source in self.raster_source]
            }
        }


class PointInPolygonFilter(VectorOperator):
    '''A PointInPolygonFilter operator.'''

    point_source: VectorOperator
    polygon_source: VectorOperator

    def __init__(self,
                 point_source: VectorOperator,
                 polygon_source: VectorOperator,
                 ):
        '''Creates a new PointInPolygonFilter filter operator.'''
        self.point_source = point_source
        self.polygon_source = polygon_source

    def name(self) -> str:
        return 'PointInPolygonFilter'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {},
            "sources": {
                "points": self.point_source.to_dict(),
                "polygons": self.polygon_source.to_dict()
            }
        }


class RasterScaling(RasterOperator):
    '''A RasterScaling operator.

    This operator scales the values of a raster by a given slope and offset.

    The scaling is done as follows:
    y = (x - offset) / slope

    The unscale mode is the inverse of the scale mode:
    x = y * slope + offset

    '''

    source: RasterOperator
    slope: Optional[Union[float, str]] = None
    offset: Optional[Union[float, str]] = None
    scaling_mode: Literal["mulSlopeAddOffset", "subOffsetDivSlope"] = "mulSlopeAddOffset"
    output_measurement: Optional[str] = None

    def __init__(self,
                 # pylint: disable=too-many-arguments
                 source: RasterOperator,
                 slope: Optional[Union[float, str]] = None,
                 offset: Optional[Union[float, str]] = None,
                 scaling_mode: Literal["mulSlopeAddOffset", "subOffsetDivSlope"] = "mulSlopeAddOffset",
                 output_measurement: Optional[str] = None
                 ):
        '''Creates a new RasterScaling operator.'''
        self.source = source
        self.slope = slope
        self.offset = offset
        self.scaling_mode = scaling_mode
        self.output_measurement = output_measurement
        if output_measurement is not None:
            raise NotImplementedError("Custom output measurement is not yet implemented")

    def name(self) -> str:
        return 'RasterScaling'

    def to_dict(self) -> Dict[str, Any]:
        def offset_scale_dict(key_or_value: Optional[Union[float, str]]) -> Dict[str, Any]:
            if key_or_value is None:
                return {"type": "auto"}

            if isinstance(key_or_value, float):
                return {"type": "constant", "value": key_or_value}

            # TODO: incorporate `domain` field
            return {"type": "metadataKey", "key": key_or_value}

        return {
            "type": self.name(),
            "params": {
                "offset": offset_scale_dict(self.offset),
                "slope": offset_scale_dict(self.slope),
                "scalingMode": self.scaling_mode
            },
            "sources": {
                "raster": self.source.to_dict()
            }
        }


class RasterTypeConversion(RasterOperator):
    '''A RasterTypeConversion operator.'''

    source: RasterOperator
    output_data_type: Literal["u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64", "f32", "f64"]

    def __init__(self,
                 source: RasterOperator,
                 output_data_type: Literal["u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64", "f32", "f64"]
                 ):
        '''Creates a new RasterTypeConversion operator.'''
        self.source = source
        self.output_data_type = output_data_type

    def name(self) -> str:
        return 'RasterTypeConversion'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "outputDataType": self.output_data_type
            },
            "sources": {
                "raster": self.source.to_dict()
            }
        }


class Reprojection(Operator):
    '''A Reprojection operator.'''
    source: Operator
    target_spatial_reference: str

    def __init__(self,
                 source: Operator,
                 target_spatial_reference: str
                 ):
        '''Creates a new Reprojection operator.'''
        self.source = source
        self.target_spatial_reference = target_spatial_reference

    def data_type(self) -> Literal['Raster', 'Vector']:
        return self.source.data_type()

    def name(self) -> str:
        return 'Reprojection'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "targetSpatialReference": self.target_spatial_reference
            },
            "sources": {
                "source": self.source.to_dict()
            }
        }

    def as_vector(self) -> VectorOperator:
        '''Casts this operator to a VectorOperator.'''
        if self.data_type() != 'Vector':
            raise TypeError("Cannot cast to VectorOperator")
        return cast(VectorOperator, self)

    def as_raster(self) -> RasterOperator:
        '''Casts this operator to a RasterOperator.'''
        if self.data_type() != 'Raster':
            raise TypeError("Cannot cast to RasterOperator")
        return cast(RasterOperator, self)


class Expression(RasterOperator):
    '''An Expression operator.'''

    expression: str
    sources: Dict[str, RasterOperator]
    output_type: Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"] = "F32"
    map_no_data: bool = False
    output_measurement: Optional[Measurement] = None

    def __init__(self,
                 expression: str,
                 sources: Dict[str, RasterOperator],
                 output_type: Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"] = "F32",
                 map_no_data: bool = False,
                 output_measurement: Optional[Measurement] = None,
                 ):
        '''Creates a new Expression operator.'''
        self.expression = expression
        self.sources = sources
        self.output_type = output_type
        self.map_no_data = map_no_data
        self.output_measurement = output_measurement

    def name(self) -> str:
        return 'Expression'

    def to_dict(self) -> Dict[str, Any]:
        params = {
            "expression": self.expression,
            "outputType": self.output_type,
            "mapNoData": self.map_no_data,
        }
        if self.output_measurement:
            params["outputMeasurement"] = self.output_measurement.to_api_dict()

        return {
            "type": self.name(),
            "params": params,
            "sources":
                {i: raster_source.to_dict() for i, raster_source in self.sources.items()}

        }


class TemporalRasterAggregation(RasterOperator):
    '''A TemporalRasterAggregation operator.'''

    source: RasterOperator
    aggregation_type: Literal["mean", "min", "max", "median", "count", "sum", "first", "last"]
    ignore_no_data: bool = False
    window_granularity: Literal["days", "months", "years", "hours", "minutes", "seconds", "millis"] = "days"
    window_size: int = 1
    output_type: Optional[Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"]] = None

    # pylint: disable=too-many-arguments
    def __init__(self,
                 source: RasterOperator,
                 aggregation_type: Literal["mean", "min", "max", "median", "count", "sum", "first", "last"],
                 ignore_no_data: bool = False,
                 granularity: Literal["days", "months", "years", "hours", "minutes", "seconds", "millis"] = "days",
                 window_size: int = 1,
                 output_type:
                 Optional[Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"]] = None,
                 ):
        '''Creates a new TemporalRasterAggregation operator.'''
        self.source = source
        self.aggregation_type = aggregation_type
        self.ignore_no_data = ignore_no_data
        self.window_granularity = granularity
        self.window_size = window_size
        self.output_type = output_type
        # todo: add window reference

    def name(self) -> str:
        return 'TemporalRasterAggregation'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "aggregation": {
                    "type": self.aggregation_type,
                    "ignoreNoData": self.ignore_no_data,
                },
                "window": {
                    "granularity": self.window_granularity,
                    "step": self.window_size
                },
                "outputType": self.output_type
            },
            "sources": {
                "raster": self.source.to_dict()
            }
        }


class TimeShift(Operator):
    '''A RasterTypeConversion operator.'''

    source: Union[RasterOperator, VectorOperator]
    shift_type: Literal["relative", "absolute"]
    granularity: Literal["days", "months", "years", "hours", "minutes", "seconds", "millis"]
    value: int

    def __init__(self,
                 source: Union[RasterOperator, VectorOperator],
                 shift_type: Literal["relative", "absolute"],
                 granularity: Literal["days", "months", "years", "hours", "minutes", "seconds", "millis"],
                 value: int,
                 ):
        '''Creates a new RasterTypeConversion operator.'''
        if shift_type == 'absolute':
            raise NotImplementedError("Absolute time shifts are not supported yet")
        self.source = source
        self.shift_type = shift_type
        self.granularity = granularity
        self.value = value

    def name(self) -> str:
        return 'TimeShift'

    def data_type(self) -> Literal['Vector', 'Raster']:
        return self.source.data_type()

    def as_vector(self) -> VectorOperator:
        '''Casts this operator to a VectorOperator.'''
        if self.data_type() != 'Vector':
            raise TypeError("Cannot cast to VectorOperator")
        return cast(VectorOperator, self)

    def as_raster(self) -> RasterOperator:
        '''Casts this operator to a RasterOperator.'''
        if self.data_type() != 'Raster':
            raise TypeError("Cannot cast to RasterOperator")
        return cast(RasterOperator, self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "type": self.shift_type,
                "granularity": self.granularity,
                "value": self.value
            },
            "sources": {
                "source": self.source.to_dict()
            }
        }
