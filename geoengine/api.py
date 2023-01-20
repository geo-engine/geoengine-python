'''The geoengine API'''
from enum import Enum
from typing import Dict, Optional, Tuple, List
from typing_extensions import Literal, TypedDict


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


class UnitlessMeasurement(Measurement):  # pylint: disable=too-few-public-methods
    '''A unitless measurement'''
    type: Literal['unitless']


class ContinuousMeasurement(Measurement):  # pylint: disable=too-few-public-methods
    '''A continuous measurement'''
    type: Literal['continuous']
    measurement: str
    unit: Optional[str]


class ClassificationMeasurement(Measurement):  # pylint: disable=too-few-public-methods
    '''A classification measurement'''
    type: Literal['classification']
    measurement: str
    classes: Dict[int, str]


class ResultDescriptor(TypedDict):  # pylint: disable=too-few-public-methods
    # TODO: add time, bbox, resolution
    '''The result descriptor of an operator'''
    type: Literal['raster', 'vector', 'plot']
    spatialReference: str


class RasterResultDescriptor(ResultDescriptor):  # pylint: disable=too-few-public-methods
    '''The result descriptor of a raster operator'''
    dataType: Literal['U8', 'U16', 'U32', 'U64', 'I8', 'I16', 'I32', 'I64', 'F32', 'F64']
    measurement: Measurement


class VectorResultDescriptor(ResultDescriptor):  # pylint: disable=too-few-public-methods
    '''The result descriptor of a vector operator'''
    dataType: Literal['MultiPoint', 'MultiLineString', 'MultiPolygon']


class PlotResultDescriptor(ResultDescriptor):  # pylint: disable=too-few-public-methods
    '''The result descriptor of a plot operator'''
    dataType: Literal['Plot']


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


class MetaDataDefinition(TypedDict):  # pylint: disable=too-few-public-methods
    '''Super class for all metadata definitions'''


class GdalMetaDataStatic(MetaDataDefinition):  # pylint: disable=too-few-public-methods
    '''Static metadata for GDAL datasets'''
    type: Literal["GdalStatic"]
    time: Optional[Tuple[str, str]]
    params: GdalDatasetParameters
    resultDescriptor: RasterResultDescriptor


class DateTimeParseFormat(TypedDict):  # pylint: disable=too-few-public-methods
    '''A format for parsing date time strings'''
    fmt: str
    hasTz: bool
    hasTime: bool


class TimeReference(Enum):  # pylint: disable=too-few-public-methods
    '''The reference for a time placeholder'''
    START = "Start"
    END = "End"


class TimeStepGranularity(Enum):  # pylint: disable=too-few-public-methods
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

    step: TimeStep
    granularity: TimeStepGranularity


class ZeroOgrSourceDurationSpec(OgrSourceDurationSpec):  # pylint: disable=too-few-public-methods
    '''A zero duration for a source duration'''
    type: Literal['zero']


class InfiniteOgrSourceDurationSpec(OgrSourceDurationSpec):
    '''An infinite duration for a source duration'''
    type: Literal['infinite']


class VectorColumnInfo(TypedDict):  # pylint: disable=too-few-public-methods
    '''A vector column info'''
    data_type: str
    measurement: Measurement


class DataId(TypedDict):  # pylint: disable=too-few-public-methods
    '''A data id'''
    type: Literal['internal', 'external']


class InternalDataId(DataId):  # pylint: disable=too-few-public-methods
    '''An internal data id'''
    type: Literal['internal']
    datasetId: str


class ExternalDataId(DataId):  # pylint: disable=too-few-public-methods
    '''An external data id'''
    type: Literal['external']
    providerId: str
    layerId: str


class ProvenanceOutput(TypedDict):  # pylint: disable=too-few-public-methods
    '''A provenance output'''
    dataId: DataId
    provenance: Provenance


class OgrSourceTimeFormat(TypedDict):  # pylint: disable=too-few-public-methods
    '''A time format for an OGR source'''
    type: Literal['seconds', 'custom', 'auto']


class SecondsOgrSourceTimeFormat(OgrSourceTimeFormat):  # pylint: disable=too-few-public-methods
    '''A seconds time format for an OGR source'''
    type: Literal['seconds']


class CustomOgrSourceTimeFormat(OgrSourceTimeFormat):  # pylint: disable=too-few-public-methods
    '''A custom time format for an OGR source'''
    type: Literal['custom']
    customFormat: str


class AutoOgrSourceTimeFormat(OgrSourceTimeFormat):  # pylint: disable=too-few-public-methods
    '''An auto time format for an OGR source'''
    type: Literal['auto']


class OgrSourceDatasetTimeType(TypedDict):  # pylint: disable=too-few-public-methods
    '''A time type for an OGR source'''
    type: Literal['start', 'start+end', 'start+duration', 'none']


class StartOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):  # pylint: disable=too-few-public-methods
    '''A start time type for an OGR source'''
    type: Literal['start']
    startFormat: OgrSourceTimeFormat
    startField: str
    duration: OgrSourceDurationSpec


class StartEndOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):  # pylint: disable=too-few-public-methods
    '''A start+end time type for an OGR source'''
    type: Literal['start+end']
    startField: str
    startFormat: OgrSourceTimeFormat
    endField: str
    endFormat: OgrSourceTimeFormat


class StartDurationOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):  # pylint: disable=too-few-public-methods
    '''A start+duration time type for an OGR source'''
    type: Literal['start+duration']


class NoneOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):  # pylint: disable=too-few-public-methods
    '''A none time type for an OGR source'''
    type: Literal['none']


class OgrOnError(Enum):  # pylint: disable=too-few-public-methods
    IGNORE = "ignore"
    ABORT = "abort"
