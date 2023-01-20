'''The geoengine API'''
from enum import Enum
from typing import Dict, Literal, Optional, Tuple, TypedDict, List


class ColorizerBreakpoint(TypedDict):
    """This class is used to generate geoengine compatible color breakpoint definitions as a dictionary."""
    value: float
    color: Tuple[int, int, int, int]


class Colorizer(TypedDict):
    """This class is used to generate geoengine compatible color map definitions as a dictionary."""
    type: Literal["linearGradient", "palette", "logarithmicGradient"]
    breakpoints: List[ColorizerBreakpoint]
    noDataColor: Tuple[int, int, int, int]
    defaultColor: Tuple[int, int, int, int]


class Provenance(TypedDict):
    '''A provenance dictionary'''
    citation: str
    license: str
    uri: str


class Symbology(TypedDict):
    '''A dictionary representation of a symbology'''
    type: Literal['vector', 'raster']


class RasterSymbology(Symbology):
    '''A dictionary representation of a raster symbology'''
    colorizer: Colorizer
    opacity: float


class AddDataset(TypedDict):
    '''The properties of a dataset'''
    id: Optional[str]
    name: str
    description: str
    sourceOperator: Literal['GdalSource']  # TODO: add more operators
    symbology: Optional[RasterSymbology]  # TODO: add vector symbology if needed
    provenance: Optional[Provenance]


class Measurement(TypedDict):
    '''A measurement'''
    type: Literal['continuous', 'classification', 'unitless']


class UnitlessMeasurement(Measurement):
    '''A unitless measurement'''
    type: Literal['unitless']


class ContinuousMeasurement(Measurement):
    '''A continuous measurement'''
    type: Literal['continuous']
    measurement: str
    unit: Optional[str]


class ClassificationMeasurement(Measurement):
    '''A classification measurement'''
    type: Literal['classification']
    measurement: str
    classes: Dict[int, str]


class ResultDescriptor(TypedDict):  # TODO: add time, bbox, resolution
    '''The result descriptor of an operator'''
    type: Literal['raster', 'vector', 'plot']
    spatialReference: str


class RasterResultDescriptor(ResultDescriptor):
    '''The result descriptor of a raster operator'''
    dataType: Literal['U8', 'U16', 'U32', 'U64', 'I8', 'I16', 'I32', 'I64', 'F32', 'F64']
    measurement: Measurement


class VectorResultDescriptor(ResultDescriptor):
    '''The result descriptor of a vector operator'''
    dataType: Literal['MultiPoint', 'MultiLineString', 'MultiPolygon']


class PlotResultDescriptor(ResultDescriptor):
    '''The result descriptor of a plot operator'''
    dataType: Literal['Plot']


class GdalDatasetGeoTransform(TypedDict):
    '''Geo transform of a GDAL dataset'''
    originCoordinate: Tuple[float, float]
    xPixelSize: float
    yPixelSize: float


class FileNotFoundHandling(str, Enum):
    NODATA = "NoData"
    ERROR = "Abort"


class RasterPropertiesKey(TypedDict):
    '''Key of a raster properties entry'''
    domain: Optional[str]
    key: str


class RasterPropertiesEntryType(Enum):
    NUMBER = "number"
    STRING = "string"


class GdalMetadataMapping(TypedDict):
    '''Mapping of GDAL metadata raster properties'''

    sourceKey: RasterPropertiesKey
    targetKey: RasterPropertiesKey
    targetType: RasterPropertiesEntryType


class GdalDatasetParameters(TypedDict):
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


class GdalMetaDataStatic(MetaDataDefinition):
    '''Static metadata for GDAL datasets'''

    type: Literal["GdalStatic"]
    time: Optional[Tuple[str, str]]
    params: GdalDatasetParameters
    resultDescriptor: RasterResultDescriptor


class DateTimeParseFormat(TypedDict):
    '''A format for parsing date time strings'''
    fmt: str
    hasTz: bool
    hasTime: bool


class TimeReference(Enum):
    '''The reference for a time placeholder'''

    START = "Start"
    END = "End"


class TimeStepGranularity(Enum):
    '''An enum of time step granularities'''
    MILLIS = 'Millis'
    SECONDS = 'Seconds'
    MINUTES = 'Minutes'
    HOURS = 'Hours'
    DAYS = 'Days'
    MONTHS = 'Months'
    YEARS = 'Years'


class TimeStep(TypedDict):
    '''A time step that consists of a granularity and a step size'''
    step: int
    granularity: TimeStepGranularity


class GdalSourceTimePlaceholder(TypedDict):
    '''A placeholder for a time value in a file name'''
    format: DateTimeParseFormat
    reference: TimeReference


class GdalMetaDataRegular(MetaDataDefinition):
    '''Metadata for regular GDAL datasets'''

    type: Literal["GdalMetaDataRegular"]
    resultDescriptor: RasterResultDescriptor
    params: GdalDatasetParameters
    timePlaceholders: Dict[str, GdalSourceTimePlaceholder]
    dataTime: Tuple[str, str]
    step: TimeStep


class GdalMetadataNetCdfCf(MetaDataDefinition):
    '''Metadata for NetCDF CF datasets'''

    type: Literal["GdalMetadataNetCdfCf"]
    resultDescriptor: RasterResultDescriptor
    params: GdalDatasetParameters
    start: str
    end: str
    step: TimeStep
    bandOffset: int


class DatasetId(TypedDict):
    '''A dataset id'''
    id: str


class UploadId(TypedDict):
    '''A upload id'''
    id: str


class VolumeId(TypedDict):
    '''A volume id'''
    id: str


class StoredDataset(TypedDict):
    '''A stored dataset'''
    dataset: str
    upload: str


class Volume(TypedDict):
    '''A volume'''
    name: str
    path: str


class OgrSourceDurationSpec(TypedDict):
    '''A duration for an OGR source'''
    type: Literal['zero', 'value', 'infinite']


class ValueOgrSourceDurationSpec(OgrSourceDurationSpec):
    '''A fixed value for a source duration'''

    step: TimeStep
    granularity: TimeStepGranularity


class ZeroOgrSourceDurationSpec(OgrSourceDurationSpec):
    '''A zero duration for a source duration'''
    type: Literal['zero']


class InfiniteOgrSourceDurationSpec(OgrSourceDurationSpec):
    '''An infinite duration for a source duration'''
    type: Literal['infinite']


class VectorColumnInfo(TypedDict):
    '''A vector column info'''
    data_type: str
    measurement: Measurement


class DataId(TypedDict):
    '''A data id'''
    type: Literal['internal', 'external']


class InternalDataId(DataId):
    '''An internal data id'''
    type: Literal['internal']
    datasetId: str


class ExternalDataId(DataId):
    '''An external data id'''
    type: Literal['external']
    providerId: str
    layerId: str


class ProvenanceOutput(TypedDict):
    '''A provenance output'''
    dataId: DataId
    provenance: Provenance


class OgrSourceTimeFormat(TypedDict):
    '''A time format for an OGR source'''
    type: Literal['seconds', 'custom', 'auto']


class SecondsOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''A seconds time format for an OGR source'''
    type: Literal['seconds']


class CustomOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''A custom time format for an OGR source'''
    type: Literal['custom']
    customFormat: str


class AutoOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''An auto time format for an OGR source'''
    type: Literal['auto']


class OgrSourceDatasetTimeType(TypedDict):
    '''A time type for an OGR source'''
    type: Literal['start', 'start+end', 'start+duration', 'none']


class StartOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''A start time type for an OGR source'''
    type: Literal['start']
    startFormat: OgrSourceTimeFormat
    startField: str
    duration: OgrSourceDurationSpec


class StartEndOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''A start+end time type for an OGR source'''
    type: Literal['start+end']
    startField: str
    startFormat: OgrSourceTimeFormat
    endField: str
    endFormat: OgrSourceTimeFormat


class StartDurationOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''A start+duration time type for an OGR source'''
    type: Literal['start+duration']


class NoneOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''A none time type for an OGR source'''
    type: Literal['none']


class OgrOnError(Enum):
    IGNORE = "ignore"
    ABORT = "abort"
