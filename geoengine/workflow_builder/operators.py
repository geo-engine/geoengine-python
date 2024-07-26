'''This module contains helpers to create workflow operators for the Geo Engine API.'''
from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, cast, Literal
import datetime
import numpy as np

from geoengine.datasets import DatasetName
from geoengine.types import Measurement, RasterBandDescriptor

# pylint: disable=too-many-lines


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

    @classmethod
    def from_workflow_dict(cls, workflow) -> Operator:
        '''Returns an operator from a workflow dictionary.'''
        if workflow['type'] == 'Raster':
            return RasterOperator.from_operator_dict(workflow['operator'])
        if workflow['type'] == 'Vector':
            return VectorOperator.from_operator_dict(workflow['operator'])

        raise NotImplementedError(f"Unknown workflow type {workflow['type']}")


class RasterOperator(Operator):
    '''Base class for all raster operators.'''

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    def data_type(self) -> Literal['Raster', 'Vector']:
        return 'Raster'

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> RasterOperator:  # pylint: disable=too-many-return-statements
        '''Returns an operator from a dictionary.'''
        if operator_dict['type'] == 'GdalSource':
            return GdalSource.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'RasterScaling':
            return RasterScaling.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'RasterTypeConversion':
            return RasterTypeConversion.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'Reprojection':
            return Reprojection.from_operator_dict(operator_dict).as_raster()
        if operator_dict['type'] == 'Interpolation':
            return Interpolation.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'Expression':
            return Expression.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'BandwiseExpression':
            return BandwiseExpression.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'TimeShift':
            return TimeShift.from_operator_dict(operator_dict).as_raster()
        if operator_dict['type'] == 'TemporalRasterAggregation':
            return TemporalRasterAggregation.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'RasterStacker':
            return RasterStacker.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'Onnx':
            return RasterOnnxClassifier.from_operator_dict(operator_dict)

        raise NotImplementedError(f"Unknown operator type {operator_dict['type']}")


class VectorOperator(Operator):
    '''Base class for all vector operators.'''

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    def data_type(self) -> Literal['Raster', 'Vector']:
        return 'Vector'

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> VectorOperator:
        '''Returns an operator from a dictionary.'''
        if operator_dict['type'] == 'OgrSource':
            return OgrSource.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'Reprojection':
            return Reprojection.from_operator_dict(operator_dict).as_vector()
        if operator_dict['type'] == 'RasterVectorJoin':
            return RasterVectorJoin.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'PointInPolygonFilter':
            return PointInPolygonFilter.from_operator_dict(operator_dict)
        if operator_dict['type'] == 'TimeShift':
            return TimeShift.from_operator_dict(operator_dict).as_vector()
        if operator_dict['type'] == 'VectorExpression':
            return VectorExpression.from_operator_dict(operator_dict)
        raise NotImplementedError(f"Unknown operator type {operator_dict['type']}")


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

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> GdalSource:
        '''Returns an operator from a dictionary.'''
        if operator_dict["type"] != "GdalSource":
            raise ValueError("Invalid operator type")

        return GdalSource(cast(str, operator_dict['params']['data']))


class OgrSource(VectorOperator):
    '''An OGR source operator.'''
    dataset: str
    attribute_projection: Optional[str] = None
    attribute_filters: Optional[str] = None

    def __init__(
            self,
            dataset: Union[str, DatasetName],
            attribute_projection: Optional[str] = None,
            attribute_filters: Optional[str] = None
    ):
        '''Creates a new OGR source operator.'''
        if isinstance(dataset, DatasetName):
            dataset = str(dataset)
        self.dataset = dataset
        self.attribute_projection = attribute_projection
        self.attribute_filters = attribute_filters

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

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> OgrSource:
        '''Returns an operator from a dictionary.'''
        if operator_dict["type"] != "OgrSource":
            raise ValueError("Invalid operator type")

        params = operator_dict['params']
        return OgrSource(
            cast(str, params['data']),
            attribute_projection=cast(Optional[str], params.get('attributeProjection')),
            attribute_filters=cast(Optional[str], params.get('attributeFilters')),
        )


class Interpolation(RasterOperator):
    '''An interpolation operator.'''
    source: RasterOperator
    interpolation: Literal["biLinear", "nearestNeighbor"] = "biLinear"
    input_resolution: Optional[Tuple[float, float]] = None

    def __init__(
        self,
            source_operator: RasterOperator,
            interpolation: Literal["biLinear", "nearestNeighbor"] = "biLinear",
            input_resolution: Optional[Tuple[float, float]] = None
    ):
        '''Creates a new interpolation operator.'''
        self.source = source_operator
        self.interpolation = interpolation
        self.input_resolution = input_resolution

    def name(self) -> str:
        return 'Interpolation'

    def to_dict(self) -> Dict[str, Any]:

        input_res: Dict[str, Union[str, float]]
        if self.input_resolution is None:
            input_res = {
                "type": "source"
            }
        else:
            input_res = {
                "type": "value",
                "x": self.input_resolution[0],
                "y": self.input_resolution[1]
            }

        return {
            "type": self.name(),
            "params": {
                "interpolation": self.interpolation,
                "inputResolution": input_res
            },
            "sources": {
                "raster": self.source.to_dict()
            }
        }

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> Interpolation:
        '''Returns an operator from a dictionary.'''
        if operator_dict["type"] != "Interpolation":
            raise ValueError("Invalid operator type")

        source = RasterOperator.from_operator_dict(cast(Dict[str, Any], operator_dict['sources']['raster']))

        def parse_input_params(params: Dict[str, Any]) -> Optional[Tuple[float, float]]:
            if 'type' not in params:
                return None
            if params['type'] == 'source':
                return None
            if params['type'] == 'value':
                return (float(params['x']), float(params['y']))
            raise ValueError(f"Invalid input resolution type {params['type']}")

        input_resolution = parse_input_params(cast(Dict[str, Any], operator_dict['params']['inputResolution']))

        return Interpolation(
            source_operator=source,
            interpolation=cast(Literal["biLinear", "nearestNeighbor"], operator_dict['params']['interpolation']),
            input_resolution=input_resolution
        )


class ColumnNames:
    '''Base class for deriving column names from bands of a raster.'''

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    def from_dict(cls, rename_dict: Dict[str, Any]) -> 'ColumnNames':
        '''Returns a ColumnNames object from a dictionary.'''
        if rename_dict["type"] == "default":
            return ColumnNamesDefault()
        if rename_dict["type"] == "suffix":
            return ColumnNamesSuffix(cast(List[str], rename_dict["values"]))
        if rename_dict["type"] == "names":
            return ColumnNamesNames(cast(List[str], rename_dict["values"]))
        raise ValueError("Invalid rename type")

    @classmethod
    def default(cls) -> 'ColumnNames':
        return ColumnNamesDefault()

    @classmethod
    def suffix(cls, values: List[str]) -> 'ColumnNames':
        return ColumnNamesSuffix(values)

    @classmethod
    def rename(cls, values: List[str]) -> 'ColumnNames':
        return ColumnNamesNames(values)


class ColumnNamesDefault(ColumnNames):
    '''column names with default suffix.'''

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "default"
        }


class ColumnNamesSuffix(ColumnNames):
    '''Rename bands with custom suffixes.'''

    suffixes: List[str]

    def __init__(self, suffixes: List[str]) -> None:
        self.suffixes = suffixes
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "suffix",
            "values": self.suffixes
        }


class ColumnNamesNames(ColumnNames):
    '''Rename bands with new names.'''

    new_names: List[str]

    def __init__(self, new_names: List[str]) -> None:
        self.new_names = new_names
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "names",
            "values": self.new_names
        }


class RasterVectorJoin(VectorOperator):
    '''A RasterVectorJoin operator.'''
    raster_sources: List[RasterOperator]
    vector_source: VectorOperator
    names: ColumnNames
    temporal_aggregation: Literal["none", "first", "mean"] = "none"
    temporal_aggregation_ignore_nodata: bool = False
    feature_aggregation: Literal["first", "mean"] = "mean"
    feature_aggregation_ignore_nodata: bool = False

    # pylint: disable=too-many-arguments
    def __init__(self,
                 raster_sources: List[RasterOperator],
                 vector_source: VectorOperator,
                 names: ColumnNames,
                 temporal_aggregation: Literal["none", "first", "mean"] = "none",
                 temporal_aggregation_ignore_nodata: bool = False,
                 feature_aggregation: Literal["first", "mean"] = "mean",
                 feature_aggregation_ignore_nodata: bool = False,
                 ):
        '''Creates a new RasterVectorJoin operator.'''
        self.raster_source = raster_sources
        self.vector_source = vector_source
        self.names = names
        self.temporal_aggregation = temporal_aggregation
        self.temporal_aggregation_ignore_nodata = temporal_aggregation_ignore_nodata
        self.feature_aggregation = feature_aggregation
        self.feature_aggregation_ignore_nodata = feature_aggregation_ignore_nodata

    def name(self) -> str:
        return 'RasterVectorJoin'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "names": self.names.to_dict(),
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

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> 'RasterVectorJoin':
        '''Returns an operator from a dictionary.'''
        if operator_dict["type"] != "RasterVectorJoin":
            raise ValueError("Invalid operator type")

        vector_source = VectorOperator.from_operator_dict(cast(Dict[str, Any], operator_dict['sources']['vector']))
        raster_sources = [
            RasterOperator.from_operator_dict(raster_source) for raster_source in cast(
                List[Dict[str, Any]], operator_dict['sources']['rasters']
            )
        ]

        params = operator_dict['params']
        return RasterVectorJoin(
            raster_sources=raster_sources,
            vector_source=vector_source,
            names=ColumnNames.from_dict(params['names']),
            temporal_aggregation=cast(Literal["none", "first", "mean"], params['temporalAggregation']),
            temporal_aggregation_ignore_nodata=cast(bool, params['temporalAggregationIgnoreNoData']),
            feature_aggregation=cast(Literal["first", "mean"], params['featureAggregation']),
            feature_aggregation_ignore_nodata=cast(bool, params['featureAggregationIgnoreNoData']),
        )


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

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> PointInPolygonFilter:
        '''Returns an operator from a dictionary.'''
        if operator_dict["type"] != "PointInPolygonFilter":
            raise ValueError("Invalid operator type")

        point_source = VectorOperator.from_operator_dict(cast(Dict[str, Any], operator_dict['sources']['points']))
        polygon_source = VectorOperator.from_operator_dict(cast(Dict[str, Any], operator_dict['sources']['polygons']))

        return PointInPolygonFilter(
            point_source=point_source,
            polygon_source=polygon_source,
        )


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

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> 'RasterScaling':
        if operator_dict["type"] != "RasterScaling":
            raise ValueError("Invalid operator type")

        source_operator = RasterOperator.from_operator_dict(operator_dict["sources"]["raster"])
        params = operator_dict["params"]

        def offset_slope_reverse(key_or_value: Optional[Dict[str, Any]]) -> Optional[Union[float, str]]:
            if key_or_value is None:
                return None
            if key_or_value["type"] == "constant":
                return key_or_value["value"]
            if key_or_value["type"] == "metadataKey":
                return key_or_value["key"]
            return None

        return RasterScaling(
            source_operator,
            slope=offset_slope_reverse(params["slope"]),
            offset=offset_slope_reverse(params["offset"]),
            scaling_mode=params["scalingMode"],
            output_measurement=params.get("outputMeasurement", None)
        )


class RasterTypeConversion(RasterOperator):
    '''A RasterTypeConversion operator.'''

    source: RasterOperator
    output_data_type: Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"]

    def __init__(self,
                 source: RasterOperator,
                 output_data_type: Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"]
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

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> 'RasterTypeConversion':
        if operator_dict["type"] != "RasterTypeConversion":
            raise ValueError("Invalid operator type")

        source_operator = RasterOperator.from_operator_dict(operator_dict["sources"]["raster"])

        return RasterTypeConversion(
            source_operator,
            output_data_type=operator_dict["params"]["outputDataType"]
        )


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

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> 'Reprojection':
        '''Constructs the operator from the given dictionary.'''
        if operator_dict["type"] != "Reprojection":
            raise ValueError("Invalid operator type")

        source_operator: Union[RasterOperator, VectorOperator]
        try:
            source_operator = RasterOperator.from_operator_dict(operator_dict["sources"]["source"])
        except ValueError:
            source_operator = VectorOperator.from_operator_dict(operator_dict["sources"]["source"])

        return Reprojection(
            source=cast(Operator, source_operator),
            target_spatial_reference=operator_dict["params"]["targetSpatialReference"]
        )


class Expression(RasterOperator):
    '''An Expression operator.'''

    expression: str
    source: RasterOperator
    output_type: Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"] = "F32"
    map_no_data: bool = False
    output_band: Optional[RasterBandDescriptor] = None

    # pylint: disable=too-many-arguments
    def __init__(self,
                 expression: str,
                 source: RasterOperator,
                 output_type: Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"] = "F32",
                 map_no_data: bool = False,
                 output_band: Optional[RasterBandDescriptor] = None,
                 ):
        '''Creates a new Expression operator.'''
        self.expression = expression
        self.source = source
        self.output_type = output_type
        self.map_no_data = map_no_data
        self.output_band = output_band

    def name(self) -> str:
        return 'Expression'

    def to_dict(self) -> Dict[str, Any]:
        params = {
            "expression": self.expression,
            "outputType": self.output_type,
            "mapNoData": self.map_no_data,
        }
        if self.output_band:
            params["outputBand"] = self.output_band.to_api_dict()

        return {
            "type": self.name(),
            "params": params,
            "sources": {
                "raster": self.source.to_dict()
            }
        }

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> 'Expression':
        if operator_dict["type"] != "Expression":
            raise ValueError("Invalid operator type")

        output_band = None
        if "output_band" in operator_dict["params"]:
            output_band = RasterBandDescriptor.from_response(operator_dict["params"]["outputBand"])

        return Expression(
            expression=operator_dict["params"]["expression"],
            source=RasterOperator.from_operator_dict(operator_dict["sources"]["raster"]),
            output_type=operator_dict["params"]["outputType"],
            map_no_data=operator_dict["params"]["mapNoData"],
            output_band=output_band
        )


class BandwiseExpression(RasterOperator):
    '''A bandwise Expression operator.'''

    expression: str
    source: RasterOperator
    output_type: Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"] = "F32"
    map_no_data: bool = False

    # pylint: disable=too-many-arguments
    def __init__(self,
                 expression: str,
                 source: RasterOperator,
                 output_type: Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"] = "F32",
                 map_no_data: bool = False,
                 ):
        '''Creates a new Expression operator.'''
        self.expression = expression
        self.source = source
        self.output_type = output_type
        self.map_no_data = map_no_data

    def name(self) -> str:
        return 'Expression'

    def to_dict(self) -> Dict[str, Any]:
        params = {
            "expression": self.expression,
            "outputType": self.output_type,
            "mapNoData": self.map_no_data,
        }

        return {
            "type": self.name(),
            "params": params,
            "sources": {
                "raster": self.source.to_dict()
            }
        }

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> 'BandwiseExpression':
        if operator_dict["type"] != "BandwiseExpression":
            raise ValueError("Invalid operator type")

        return BandwiseExpression(
            expression=operator_dict["params"]["expression"],
            source=RasterOperator.from_operator_dict(operator_dict["sources"]["raster"]),
            output_type=operator_dict["params"]["outputType"],
            map_no_data=operator_dict["params"]["mapNoData"],
        )


class GeoVectorDataType(Enum):
    '''The output type of geometry vector data.'''
    MULTI_POINT = "MultiPoint"
    MULTI_LINE_STRING = "MultiLineString"
    MULTI_POLYGON = "MultiPolygon"


class VectorExpression(VectorOperator):
    '''The `VectorExpression` operator.'''

    source: VectorOperator

    expression: str
    input_columns: List[str]
    output_column: str | GeoVectorDataType
    geometry_column_name = None
    output_measurement: Optional[Measurement] = None

    # pylint: disable=too-many-arguments
    def __init__(self,
                 source: VectorOperator,
                 *,
                 expression: str,
                 input_columns: List[str],
                 output_column: str | GeoVectorDataType,
                 geometry_column_name: Optional[str] = None,
                 output_measurement: Optional[Measurement] = None,
                 ):
        '''Creates a new VectorExpression operator.'''
        self.source = source

        self.expression = expression
        self.input_columns = input_columns
        self.output_column = output_column

        self.geometry_column_name = geometry_column_name
        self.output_measurement = output_measurement

    def name(self) -> str:
        return 'VectorExpression'

    def to_dict(self) -> Dict[str, Any]:
        if isinstance(self.output_column, GeoVectorDataType):
            output_column_dict = {
                "type": "geometry",
                "value": self.output_column.value,
            }
        elif isinstance(self.output_column, str):
            output_column_dict = {
                "type": "column",
                "value": self.output_column,
            }

        params = {
            "expression": self.expression,
            "inputColumns": self.input_columns,
            "outputColumn": output_column_dict,
        }

        if self.geometry_column_name:
            params["geometryColumnName"] = self.geometry_column_name

        if self.output_measurement:
            params["outputMeasurement"] = self.output_measurement.to_api_dict().to_dict()

        return {
            "type": self.name(),
            "params": params,
            "sources": {
                "vector": self.source.to_dict()
            }
        }

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> VectorExpression:
        if operator_dict["type"] != "Expression":
            raise ValueError("Invalid operator type")

        geometry_column_name = None
        if "geometryColumnName" in operator_dict["params"]:
            geometry_column_name = operator_dict["params"]["geometryColumnName"]

        output_measurement = None
        if "outputMeasurement" in operator_dict["params"]:
            output_measurement = Measurement.from_response(operator_dict["params"]["outputMeasurement"])

        return VectorExpression(
            source=VectorOperator.from_operator_dict(operator_dict["sources"]["vector"]),
            expression=operator_dict["params"]["expression"],
            input_columns=operator_dict["params"]["inputColumns"],
            output_column=operator_dict["params"]["outputColumn"],
            geometry_column_name=geometry_column_name,
            output_measurement=output_measurement,
        )


class TemporalRasterAggregation(RasterOperator):
    '''A TemporalRasterAggregation operator.'''
    # pylint: disable=too-many-instance-attributes

    source: RasterOperator
    aggregation_type: Literal["mean", "min", "max", "median", "count", "sum", "first", "last", "percentileEstimate"]
    ignore_no_data: bool = False
    window_granularity: Literal["days", "months", "years", "hours", "minutes", "seconds", "millis"] = "days"
    window_size: int = 1
    output_type: Optional[Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"]] = None
    percentile: Optional[float] = None
    window_ref: Optional[np.datetime64] = None

    # pylint: disable=too-many-arguments
    def __init__(self,
                 source: RasterOperator,
                 aggregation_type:
                 Literal["mean", "min", "max", "median", "count", "sum", "first", "last", "percentileEstimate"],
                 ignore_no_data: bool = False,
                 granularity: Literal["days", "months", "years", "hours", "minutes", "seconds", "millis"] = "days",
                 window_size: int = 1,
                 output_type:
                 Optional[Literal["U8", "U16", "U32", "U64", "I8", "I16", "I32", "I64", "F32", "F64"]] = None,
                 percentile: Optional[float] = None,
                 window_reference: Optional[Union[datetime.datetime, np.datetime64]] = None
                 ):
        '''Creates a new TemporalRasterAggregation operator.'''
        self.source = source
        self.aggregation_type = aggregation_type
        self.ignore_no_data = ignore_no_data
        self.window_granularity = granularity
        self.window_size = window_size
        self.output_type = output_type
        if self.aggregation_type == "percentileEstimate":
            if percentile is None:
                raise ValueError("Percentile must be set for percentileEstimate")
            if percentile <= 0.0 or percentile > 1.0:
                raise ValueError("Percentile must be > 0.0 and <= 1.0")
            self.percentile = percentile
        if window_reference is not None:
            if isinstance(window_reference, np.datetime64):
                self.window_ref = window_reference
            elif isinstance(window_reference, datetime.datetime):
                # We assume that a datetime without a timezone means UTC
                if window_reference.tzinfo is not None:
                    window_reference = window_reference.astimezone(tz=datetime.timezone.utc).replace(tzinfo=None)
                self.window_ref = np.datetime64(window_reference)
            else:
                raise ValueError("`window_reference` must be of type `datetime.datetime` or `numpy.datetime64`")

    def name(self) -> str:
        return 'TemporalRasterAggregation'

    def to_dict(self) -> Dict[str, Any]:
        w_ref = self.window_ref.astype('datetime64[ms]').astype(int) if self.window_ref is not None else None

        return {
            "type": self.name(),
            "params": {
                "aggregation": {
                    "type": self.aggregation_type,
                    "ignoreNoData": self.ignore_no_data,
                    "percentile": self.percentile
                },
                "window": {
                    "granularity": self.window_granularity,
                    "step": self.window_size
                },
                "windowReference": w_ref,
                "outputType": self.output_type
            },
            "sources": {
                "raster": self.source.to_dict()
            }
        }

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> 'TemporalRasterAggregation':
        if operator_dict["type"] != "TemporalRasterAggregation":
            raise ValueError("Invalid operator type")

        w_ref: Optional[Union[datetime.datetime, np.datetime64]] = None
        if "windowReference" in operator_dict["params"]:
            t_ref = operator_dict["params"]["windowReference"]
            if isinstance(t_ref, str):
                w_ref = datetime.datetime.fromisoformat(t_ref)
            if isinstance(t_ref, int):
                w_ref = np.datetime64(t_ref, 'ms')

        percentile = None
        if "percentile" in operator_dict["params"]["aggregation"]:
            percentile = operator_dict["params"]["aggregation"]["percentile"]

        return TemporalRasterAggregation(
            source=RasterOperator.from_operator_dict(operator_dict["sources"]["raster"]),
            aggregation_type=operator_dict["params"]["aggregation"]["type"],
            ignore_no_data=operator_dict["params"]["aggregation"]["ignoreNoData"],
            granularity=operator_dict["params"]["window"]["granularity"],
            window_size=operator_dict["params"]["window"]["step"],
            output_type=operator_dict["params"]["outputType"],
            window_reference=w_ref,
            percentile=percentile
        )


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

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> 'TimeShift':
        '''Constructs the operator from the given dictionary.'''
        if operator_dict["type"] != "TimeShift":
            raise ValueError("Invalid operator type")
        source: Union[RasterOperator, VectorOperator]
        try:
            source = VectorOperator.from_operator_dict(operator_dict["sources"]["source"])
        except ValueError:
            source = RasterOperator.from_operator_dict(operator_dict["sources"]["source"])

        return TimeShift(
            source=source,
            shift_type=operator_dict["params"]["type"],
            granularity=operator_dict["params"]["granularity"],
            value=operator_dict["params"]["value"]
        )


class RenameBands:
    '''Base class for renaming bands of a raster.'''

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    def from_dict(cls, rename_dict: Dict[str, Any]) -> 'RenameBands':
        '''Returns a RenameBands object from a dictionary.'''
        if rename_dict["type"] == "default":
            return RenameBandsDefault()
        if rename_dict["type"] == "suffix":
            return RenameBandsSuffix(cast(List[str], rename_dict["values"]))
        if rename_dict["type"] == "rename":
            return RenameBandsRename(cast(List[str], rename_dict["values"]))
        raise ValueError("Invalid rename type")

    @classmethod
    def default(cls) -> 'RenameBands':
        return RenameBandsDefault()

    @classmethod
    def suffix(cls, values: List[str]) -> 'RenameBands':
        return RenameBandsSuffix(values)

    @classmethod
    def rename(cls, values: List[str]) -> 'RenameBands':
        return RenameBandsRename(values)


class RenameBandsDefault(RenameBands):
    '''Rename bands with default suffix.'''

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "default"
        }


class RenameBandsSuffix(RenameBands):
    '''Rename bands with custom suffixes.'''

    suffixes: List[str]

    def __init__(self, suffixes: List[str]) -> None:
        self.suffixes = suffixes
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "suffix",
            "values": self.suffixes
        }


class RenameBandsRename(RenameBands):
    '''Rename bands with new names.'''

    new_names: List[str]

    def __init__(self, new_names: List[str]) -> None:
        self.new_names = new_names
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "rename",
            "values": self.new_names
        }


class RasterStacker(RasterOperator):
    '''The RasterStacker operator.'''

    sources: List[RasterOperator]
    rename: RenameBands

    # pylint: disable=too-many-arguments
    def __init__(self,
                 sources: List[RasterOperator],
                 rename: RenameBands = RenameBandsDefault()
                 ):
        '''Creates a new RasterStacker operator.'''
        self.sources = sources
        self.rename = rename

    def name(self) -> str:
        return 'RasterStacker'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "renameBands": self.rename.to_dict()
            },
            "sources": {
                "rasters": [raster_source.to_dict() for raster_source in self.sources]
            }
        }

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> 'RasterStacker':
        if operator_dict["type"] != "RasterStacker":
            raise ValueError("Invalid operator type")

        sources = [RasterOperator.from_operator_dict(source) for source in operator_dict["sources"]["rasters"]]
        rename = RenameBands.from_dict(operator_dict["params"]["renameBands"])

        return RasterStacker(
            sources=sources,
            rename=rename
        )


class RasterOnnxClassifier(RasterOperator):
    '''A raster operator that applies an onnx model.'''

    source: RasterOperator
    model_name: str

    def __init__(self,
                 source: RasterOperator,
                 model_name: str,
                 ):
        '''Creates a new RasterOnnxClassifier operator.'''
        self.source = source
        self.model_name = model_name

    def name(self) -> str:
        return 'Onnx'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.name(),
            "params": {
                "model": self.model_name,
            },
            "sources": {
                "raster": self.source.to_dict()
            }
        }

    @classmethod
    def from_operator_dict(cls, operator_dict: Dict[str, Any]) -> 'RasterOnnxClassifier':
        if operator_dict["type"] != "Onnx":
            raise ValueError("Invalid operator type")

        source_operator = RasterOperator.from_operator_dict(operator_dict["sources"]["raster"])

        return RasterOnnxClassifier(
            source_operator,
            model_name=operator_dict["params"]["model"]
        )
