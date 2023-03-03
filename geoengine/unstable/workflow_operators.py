'''This module contains helpers to create operators for the GeoEngine API.'''

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union, cast
from typing_extensions import Literal


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

    def __init__(self, dataset: str):
        '''Creates a new GDAL source operator.'''
        self.dataset = dataset

    def name(self) -> str:
        return 'GdalSource'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.name(),
            'params': {
                "data": {
                    "type": "internal",
                    "datasetId": self.dataset,
                }
            }
        }


class OgrSource(VectorOperator):
    '''An OGR source operator.'''
    dataset: str
    attribute_projection: Optional[str] = None
    attribute_filters: Optional[str] = None

    def __init__(self, dataset: str):
        '''Creates a new OGR source operator.'''
        self.dataset = dataset

    def name(self) -> str:
        return 'OgrSource'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.name(),
            'params': {
                "data": {
                    "type": "internal",
                    "datasetId": self.dataset,
                },
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
    feature_aggregation: Literal["first", "mean"] = "mean"

    def __init__(self,
                 raster_sources: List[RasterOperator],
                 vector_source: VectorOperator,
                 new_column_names: List[str],
                 temporal_aggregation: Literal["none", "first", "mean"] = "none",
                 feature_aggregation: Literal["first", "mean"] = "mean"
                 ):
        '''Creates a new RasterVectorJoin operator.'''
        self.raster_source = raster_sources
        self.vector_source = vector_source
        self.new_column_names = new_column_names
        self.temporal_aggregation = temporal_aggregation
        self.feature_aggregation = feature_aggregation
        assert (len(self.raster_source) == len(self.new_column_names))

    def name(self) -> str:
        return 'RasterVectorJoin'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "names": self.new_column_names,
                "temporalAggregation": self.temporal_aggregation,
                "featureAggregation": self.feature_aggregation,
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
    slope_key_or_value: Optional[Union[float, str]] = None
    offset_key_or_value: Optional[Union[float, str]] = None
    scaling_mode: Literal["scale", "unscale"] = "scale"
    output_measurement: Optional[str] = None

    def __init__(self,
                 source: RasterOperator,
                 slope_key_or_value: Optional[Union[float, str]] = None,
                 offset_key_or_value: Optional[Union[float, str]] = None,
                 scaling_mode: Literal["scale", "unscale"] = "scale",
                 output_measurement: Optional[str] = None
                 ):
        '''Creates a new RasterScaling operator.'''
        self.source = source
        self.slope_key_or_value = slope_key_or_value
        self.offset_key_or_value = offset_key_or_value
        self.scaling_mode = scaling_mode
        self.output_measurement = output_measurement

    def name(self) -> str:
        return 'RasterScaling'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "offsetKeyOrValue": self.offset_key_or_value,
                "scaleKeyOrValue": self.slope_key_or_value,
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
