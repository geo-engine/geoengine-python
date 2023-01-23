'''The geoengine API'''
from enum import Enum
from typing import Dict, Optional, Tuple, List, Union
from typing_extensions import Literal, TypedDict


class Coordinate2D(TypedDict):  # pylint: disable=too-few-public-methods
    '''A coordinate with x, y coordinates'''
    x: float
    y: float


class SpatialResolution(TypedDict):  # pylint: disable=too-few-public-methods
    '''A spatial resolution'''
    x: float
    y: float

class TimeInterval(TypedDict):  # pylint: disable=too-few-public-methods
    '''A time interval with iso 8601 strings as start and end or unix timestamps'''
    start: Union[str, int]
    end: Optional[Union[str, int]]


class BoundingBox2D(TypedDict):  # pylint: disable=too-few-public-methods
    '''A bounding box with x, y coordinates'''
    lowerLeftCoordinate: Coordinate2D
    upperRightCoordinate: Coordinate2D


class SpatialPartition2D(TypedDict):  # pylint: disable=too-few-public-methods
    '''A spatial partition with x, y coordinates'''
    upperLeftCoordinate: Coordinate2D
    lowerRightCoordinate: Coordinate2D

class QueryRectangle(TypedDict):  # pylint: disable=too-few-public-methods
    '''A query rectangle with x, y coordinates'''
    spatialResolution: SpatialResolution
    timeInterval: TimeInterval

class RasterQueryRectangle(QueryRectangle):  # pylint: disable=too-few-public-methods
    '''A query rectangle for raster data'''
    spatialBounds: SpatialPartition2D

class VectorQueryRectangle(QueryRectangle):  # pylint: disable=too-few-public-methods
    '''A query rectangle for vector data'''
    spatialBounds: BoundingBox2D

class PlotQueryRectangle(QueryRectangle):  # pylint: disable=too-few-public-methods
    '''A query rectangle for plot data'''
    spatialBounds: BoundingBox2D

class ColorizerBreakpoint(TypedDict):  # pylint: disable=too-few-public-methods
    """This class is used to generate geoengine compatible color breakpoint definitions as a dictionary."""
    value: float
    color: Tuple[int, int, int, int]


class Colorizer(TypedDict):  # pylint: disable=too-few-public-methods
    """This class is used to generate geoengine compatible color map definitions as a dictionary."""
    type: Literal["linearGradient", "palette", "logarithmicGradient"]
    breakpoints: List[ColorizerBreakpoint]
    noDataColor: Tuple[int, int, int, int]
    defaultColor: Tuple[int, int, int, int]


class Provenance(TypedDict):  # pylint: disable=too-few-public-methods
    '''A provenance dictionary'''
    citation: str
    license: str
    uri: str


class Symbology(TypedDict):  # pylint: disable=too-few-public-methods
    '''A dictionary representation of a symbology'''
    type: Literal['vector', 'raster']


class RasterSymbology(Symbology):  # pylint: disable=too-few-public-methods
    '''A dictionary representation of a raster symbology'''
    colorizer: Colorizer
    opacity: float


class AddDataset(TypedDict):  # pylint: disable=too-few-public-methods
    '''The properties of a dataset'''
    id: Optional[str]
    name: str
    description: str
    sourceOperator: Literal['GdalSource']  # TODO: add more operators
    symbology: Optional[RasterSymbology]  # TODO: add vector symbology if needed
    provenance: Optional[Provenance]


class Measurement(TypedDict):  # pylint: disable=too-few-public-methods
    '''A measurement'''
    type: Literal['continuous', 'classification', 'unitless']


class ContinuousMeasurement(Measurement):  # pylint: disable=too-few-public-methods
    '''A continuous measurement'''
    measurement: str
    unit: Optional[str]


class ClassificationMeasurement(Measurement):  # pylint: disable=too-few-public-methods
    '''A classification measurement'''
    measurement: str
    classes: Dict[str, str]  # TODO: this are int in the backend. how is this handled here?


class GdalDatasetGeoTransform(TypedDict):  # pylint: disable=too-few-public-methods
    '''Geo transform of a GDAL dataset'''
    originCoordinate: Tuple[float, float]
    xPixelSize: float
    yPixelSize: float


class FileNotFoundHandling(str, Enum):  # pylint: disable=too-few-public-methods
    NODATA = "NoData"
    ERROR = "Abort"


class RasterPropertiesKey(TypedDict):  # pylint: disable=too-few-public-methods
    '''Key of a raster properties entry'''
    domain: Optional[str]
    key: str


class RasterPropertiesEntryType(Enum):  # pylint: disable=too-few-public-methods
    NUMBER = "number"
    STRING = "string"


class GdalMetadataMapping(TypedDict):  # pylint: disable=too-few-public-methods
    '''Mapping of GDAL metadata raster properties'''

    sourceKey: RasterPropertiesKey
    targetKey: RasterPropertiesKey
    targetType: RasterPropertiesEntryType


class GdalDatasetParameters(TypedDict):  # pylint: disable=too-few-public-methods
    '''Parameters for a GDAL dataset'''
    filePath: str
    rasterbandChannel: int
    geoTransform: GdalDatasetGeoTransform
    width: int
    height: int
    fileNotFoundHandling: FileNotFoundHandling
    noDataValue: Optional[float]
    propertiesMapping: Optional[List[GdalMetadataMapping]]
    gdalOpenOptions: Optional[List[str]]
    gdalConfigOptions: Optional[List[Tuple[str, str]]]
    allowAlphabandAsMask: bool


class DateTimeParseFormat(TypedDict):  # pylint: disable=too-few-public-methods
    '''A format for parsing date time strings'''
    fmt: str
    hasTz: bool
    hasTime: bool


class TimeReference(Enum):  # pylint: disable=too-few-public-methods
    '''The reference for a time placeholder'''
    START = "Start"
    END = "End"


class TimeStepGranularity(str, Enum):  # pylint: disable=too-few-public-methods
    '''An enum of time step granularities'''
    MILLIS = 'Millis'
    SECONDS = 'Seconds'
    MINUTES = 'Minutes'
    HOURS = 'Hours'
    DAYS = 'Days'
    MONTHS = 'Months'
    YEARS = 'Years'


class TimeStep(TypedDict):  # pylint: disable=too-few-public-methods
    '''A time step that consists of a granularity and a step size'''
    step: int
    granularity: TimeStepGranularity


class GdalSourceTimePlaceholder(TypedDict):  # pylint: disable=too-few-public-methods
    '''A placeholder for a time value in a file name'''
    format: DateTimeParseFormat
    reference: TimeReference


class DatasetId(TypedDict):  # pylint: disable=too-few-public-methods
    '''A dataset id'''
    id: str


class UploadId(TypedDict):  # pylint: disable=too-few-public-methods
    '''A upload id'''
    id: str


class VolumeId(TypedDict):  # pylint: disable=too-few-public-methods
    '''A volume id'''
    id: str


class StoredDataset(TypedDict):  # pylint: disable=too-few-public-methods
    '''A stored dataset'''
    dataset: str
    upload: str


class Volume(TypedDict):  # pylint: disable=too-few-public-methods
    '''A volume'''
    name: str
    path: str


class OgrSourceDurationSpec(TypedDict):  # pylint: disable=too-few-public-methods
    '''A duration for an OGR source'''
    type: Literal['zero', 'value', 'infinite']


class ValueOgrSourceDurationSpec(OgrSourceDurationSpec):  # pylint: disable=too-few-public-methods
    '''A fixed value for a source duration'''
    step: int
    granularity: TimeStepGranularity


class VectorColumnInfo(TypedDict):  # pylint: disable=too-few-public-methods
    '''A vector column info'''
    dataType: str
    measurement: Measurement


class ResultDescriptor(TypedDict):  # pylint: disable=too-few-public-methods
    # TODO: add time, bbox, resolution
    '''The result descriptor of an operator'''
    type: Literal['raster', 'vector', 'plot']
    time: Optional[TimeInterval]
    resolution: Optional[SpatialResolution]


class RasterResultDescriptor(ResultDescriptor):  # pylint: disable=too-few-public-methods
    '''The result descriptor of a raster operator'''
    spatialReference: str
    dataType: Literal['U8', 'U16', 'U32', 'U64', 'I8', 'I16', 'I32', 'I64', 'F32', 'F64']
    measurement: Measurement
    bbox: Optional[SpatialPartition2D]

class VectorResultDescriptor(ResultDescriptor):  # pylint: disable=too-few-public-methods
    '''The result descriptor of a vector operator'''
    spatialReference: str
    dataType: Literal['MultiPoint', 'MultiLineString', 'MultiPolygon']
    columns: Dict[str, VectorColumnInfo]
    bbox: Optional[BoundingBox2D]



class PlotResultDescriptor(ResultDescriptor):  # pylint: disable=too-few-public-methods
    '''The result descriptor of a plot operator'''
    spatialReference: str
    dataType: Literal['Plot']
    bbox: Optional[BoundingBox2D]


class MetaDataDefinition(TypedDict):  # pylint: disable=too-few-public-methods
    '''Super class for all metadata definitions'''


class GdalMetaDataStatic(MetaDataDefinition):  # pylint: disable=too-few-public-methods
    '''Static metadata for GDAL datasets'''
    type: Literal["GdalStatic"]
    time: Optional[Tuple[str, str]]
    params: GdalDatasetParameters
    resultDescriptor: RasterResultDescriptor


class GdalMetaDataRegular(MetaDataDefinition):  # pylint: disable=too-few-public-methods
    '''Metadata for regular GDAL datasets'''
    type: Literal["GdalMetaDataRegular"]
    resultDescriptor: RasterResultDescriptor
    params: GdalDatasetParameters
    timePlaceholders: Dict[str, GdalSourceTimePlaceholder]
    dataTime: Tuple[str, str]
    step: TimeStep


class GdalMetadataNetCdfCf(MetaDataDefinition):  # pylint: disable=too-few-public-methods
    '''Metadata for NetCDF CF datasets'''
    type: Literal["GdalMetadataNetCdfCf"]
    resultDescriptor: RasterResultDescriptor
    params: GdalDatasetParameters
    start: str
    end: str
    step: TimeStep
    bandOffset: int

class WorkflowId(TypedDict):  # pylint: disable=too-few-public-methods
    '''A data id'''
    id: str

class DataId(TypedDict):  # pylint: disable=too-few-public-methods
    '''A data id'''
    type: Literal['internal', 'external']


class InternalDataId(DataId):  # pylint: disable=too-few-public-methods
    '''An internal data id'''
    datasetId: str


class ExternalDataId(DataId):  # pylint: disable=too-few-public-methods
    '''An external data id'''
    providerId: str
    layerId: str


class ProvenanceOutput(TypedDict):  # pylint: disable=too-few-public-methods
    '''A provenance output'''
    data: DataId
    provenance: Provenance


class OgrSourceTimeFormat(TypedDict):  # pylint: disable=too-few-public-methods
    '''A time format for an OGR source'''
    format: Literal['unixTimeStamp', 'custom', 'auto']


class CustomOgrSourceTimeFormat(OgrSourceTimeFormat):  # pylint: disable=too-few-public-methods
    '''A custom time format for an OGR source'''
    customFormat: str


class UnixTimeStampType(Enum):
    '''A unix time stamp type'''
    EPOCHSECONDS = 'epochSeconds'
    EPOCHMILLISECONDS = 'epochMilliseconds'


class UnixTimeStampOgrSourceTimeFormat(OgrSourceTimeFormat):  # pylint: disable=too-few-public-methods
    '''A unix time stamp time format for an OGR source'''
    timestampType: UnixTimeStampType


class OgrSourceDatasetTimeType(TypedDict):  # pylint: disable=too-few-public-methods
    '''A time type for an OGR source'''
    type: Literal['start', 'start+end', 'start+duration', 'none']


class StartOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):  # pylint: disable=too-few-public-methods
    '''A start time type for an OGR source'''
    startFormat: OgrSourceTimeFormat
    startField: str
    duration: OgrSourceDurationSpec


class StartEndOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):  # pylint: disable=too-few-public-methods
    '''A start+end time type for an OGR source'''
    startField: str
    startFormat: OgrSourceTimeFormat
    endField: str
    endFormat: OgrSourceTimeFormat


class StartDurationOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):  # pylint: disable=too-few-public-methods
    '''A start+duration time type for an OGR source'''
    startField: str
    startFormat: OgrSourceTimeFormat
    durationField: str


class OgrOnError(Enum):  # pylint: disable=too-few-public-methods
    IGNORE = "ignore"
    ABORT = "abort"


class GeoEngineExceptionResponse(TypedDict):
    '''
    The error response from the Geo Engine
    '''
    error: str
    message: str
