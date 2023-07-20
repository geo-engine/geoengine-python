'''These types represent Geo Engine's backend API types before/after JSON (de)serialization.'''

from enum import Enum
from typing import Any, Dict, Optional, Tuple, List, Union, TypedDict, Literal
from typing_extensions import TypeAlias

Rgba: TypeAlias = Tuple[int, int, int, int]

GEOMETRY_COLUMN_NAME = '__geometry'
TIME_COLUMN_NAME = '__time'


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
    color: Rgba


class Colorizer(TypedDict):  # pylint: disable=too-few-public-methods
    """This is a color map definitions as a dictionary."""
    type: Literal["linearGradient", "palette", "logarithmicGradient"]
    noDataColor: Rgba


class PaletteColorizer(Colorizer):  # pylint: disable=too-few-public-methods
    """This is a palette color map definitions as a dictionary."""
    colors: Dict[float, Rgba]
    defaultColor: Rgba


class LinearGradientColorizer(Colorizer):  # pylint: disable=too-few-public-methods
    """This is a linear gradient color map definitions as a dictionary."""
    overColor: Rgba
    underColor: Rgba
    breakpoints: List[ColorizerBreakpoint]


class LogarithmicGradientColorizer(Colorizer):  # pylint: disable=too-few-public-methods
    """This is a logarithmic gradient color map definitions as a dictionary."""
    overColor: Rgba
    underColor: Rgba
    breakpoints: List[ColorizerBreakpoint]


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


class GeoTransform(TypedDict):  # pylint: disable=too-few-public-methods
    '''Geo transform of a GDAL dataset'''
    originCoordinate: Coordinate2D
    xPixelSize: float
    yPixelSize: float


class FileNotFoundHandling(str, Enum):  # pylint: disable=too-few-public-methods
    NODATA = "NoData"
    ERROR = "Abort"


class RasterPropertiesKey(TypedDict):  # pylint: disable=too-few-public-methods
    '''Key of a raster properties entry'''
    domain: Optional[str]
    key: str


class RasterPropertiesEntryType(str, Enum):  # pylint: disable=too-few-public-methods
    NUMBER = "number"
    STRING = "string"


class VectorDataType(str, Enum):
    '''An enum of vector data types'''

    DATA = 'Data'
    MULTI_POINT = 'MultiPoint'
    MULTI_LINE_STRING = 'MultiLineString'
    MULTI_POLYGON = 'MultiPolygon'


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
    format: str
    reference: TimeReference


class DatasetName(TypedDict):  # pylint: disable=too-few-public-methods
    '''A dataset name'''
    datasetName: str


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


class FeatureDataType(str, Enum):
    '''Vector column data type'''

    CATEGORY = "category"
    INT = "int"
    FLOAT = "float"
    TEXT = "text"
    BOOL = "bool"
    DATETIME = "dateTime"


class VectorColumnInfo(TypedDict):  # pylint: disable=too-few-public-methods
    '''A vector column info'''
    dataType: FeatureDataType
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
    dataType: VectorDataType
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


class GdalLoadingInfoTemporalSlice(TypedDict):  # pylint: disable=too-few-public-methods
    time: TimeInterval
    params: Optional[GdalDatasetParameters]


class GdalMetaDataList(MetaDataDefinition):  # pylint: disable=too-few-public-methods
    '''Metadata for a list of GDAL datasets'''
    type: Literal["GdalMetaDataList"]
    resultDescriptor: RasterResultDescriptor
    params: List[GdalLoadingInfoTemporalSlice]


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


class ProvenanceEntry(TypedDict):  # pylint: disable=too-few-public-methods
    '''A provenance entry'''
    provenance: Provenance
    data: List[DataId]


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


class OgrOnError(str, Enum):  # pylint: disable=too-few-public-methods
    IGNORE = "ignore"
    ABORT = "abort"


class GeoEngineExceptionResponse(TypedDict):  # pylint: disable=too-few-public-methods
    '''
    The error response from the Geo Engine
    '''
    error: str
    message: str


class LayerCollectionAndProviderIdResponse(TypedDict):  # pylint: disable=too-few-public-methods
    collectionId: str
    providerId: str


class LayerAndProviderIdResponse(TypedDict):  # pylint: disable=too-few-public-methods
    layerId: str
    providerId: str


class LayerCollectionListingResponse(TypedDict):  # pylint: disable=too-few-public-methods
    '''A layer collection listing response JSON from a HTTP request'''
    id: Union[LayerCollectionAndProviderIdResponse, LayerAndProviderIdResponse]
    name: str
    description: str
    type: str


class LayerCollectionResponse(TypedDict):  # pylint: disable=too-few-public-methods
    '''A layer collection response JSON from a HTTP request'''
    id: LayerCollectionAndProviderIdResponse
    name: str
    description: str
    items: List[LayerCollectionListingResponse]


class LayerResponse(TypedDict):  # pylint: disable=too-few-public-methods
    '''A layer response JSON from a HTTP request'''
    id: LayerAndProviderIdResponse
    name: str
    description: str
    workflow: Dict[str, Any]  # TODO: specify in more detail
    symbology: Optional[Symbology]
    properties: List[Any]  # TODO: specify in more detail
    metadata: Dict[Any, Any]  # TODO: specify in more detail


class OgrLoadingInfoColumns(TypedDict):  # pylint: disable=too-few-public-methods
    '''The columns of an OGR dataset'''
    x: Optional[str]
    y: Optional[str]
    float: Optional[List[str]]
    int: Optional[List[str]]
    text: Optional[List[str]]


class OgrLoadingInfo(TypedDict):  # pylint: disable=too-few-public-methods
    '''The loading info for an OGR dataset'''
    fileName: str
    layerName: str
    dataType: VectorDataType
    time: OgrSourceDatasetTimeType
    columns: OgrLoadingInfoColumns
    onError: OgrOnError


class OgrMetadata(MetaDataDefinition):  # pylint: disable=too-few-public-methods
    '''Metadata for OGR datasets'''
    type: Literal["OgrMetaData"]
    loadingInfo: OgrLoadingInfo
    resultDescriptor: VectorResultDescriptor


class AddDatasetProperties(TypedDict):  # pylint: disable=too-few-public-methods
    '''The properties of a dataset'''
    name: Optional[str]
    displayName: str
    description: str
    sourceOperator: Literal['GdalSource', 'OgrSource']  # TODO: add more operators
    symbology: Optional[RasterSymbology]  # TODO: add vector symbology if needed
    provenance: Optional[List[Provenance]]


class DatasetStorage(TypedDict):  # pylint: disable=too-few-public-methods
    '''were the dataset is stored'''


class DatasetPath(DatasetStorage):  # pylint: disable=too-few-public-methods
    '''were the dataset is stored'''
    upload: str


class DatasetVolume(DatasetStorage):  # pylint: disable=too-few-public-methods
    '''were the dataset is stored'''
    volume: str


class DatasetDefinition(TypedDict):  # pylint: disable=too-few-public-methods
    '''The definition of a dataset'''
    properties: AddDatasetProperties
    metaData: MetaDataDefinition


class CreateDataset(TypedDict):  # pylint: disable=too-few-public-methods
    '''A dataset to create'''
    dataPath: DatasetStorage
    definition: DatasetDefinition


class DatasetListing(TypedDict):  # pylint: disable=too-few-public-methods
    '''A dataset listing'''
    name: DatasetName
    display_name: str
    description: str
    tags: List[str]
    source_operator: str
    result_descriptor: ResultDescriptor
    symbology: Optional[Symbology]


class Quota(TypedDict):  # pylint: disable=too-few-public-methods
    '''Quota of a user'''
    available: int
    used: int


class UpdateQuota(TypedDict):  # pylint: disable=too-few-public-methods
    '''Update request for quota'''
    available: int


class Resource(TypedDict):  # pylint: disable=too-few-public-methods
    '''A resource id'''
    type: Literal['dataset', 'layer', 'layerCollection', 'project']
    id: str


class Permission(str, Enum):
    '''A permission'''
    READ = 'Read'
    OWNER = 'Owner'


class PermissionRequest(TypedDict):  # pylint: disable=too-few-public-methods
    '''A permission request'''
    roleId: str  # should be UUID, but UUID is not json serializable
    resource: Resource
    permission: Permission


class AddRoleRequest(TypedDict):  # pylint: disable=too-few-public-methods
    '''An add role request'''
    name: str
