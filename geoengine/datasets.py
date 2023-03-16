'''
Module for working with datasets and source definitions
'''

from __future__ import annotations
from abc import abstractmethod
from typing import Dict, List, NamedTuple, Optional, Union, cast
from enum import Enum
from uuid import UUID
import json
from typing_extensions import Literal
from attr import dataclass
import numpy as np
import geopandas as gpd
import requests as req
from geoengine import api
from geoengine.error import GeoEngineException, InputException, MissingFieldInResponseException
from geoengine.auth import get_session
from geoengine.types import Provenance, RasterSymbology, TimeStep, \
    TimeStepGranularity, VectorDataType, VectorResultDescriptor, VectorColumnInfo, \
    UnitlessMeasurement, FeatureDataType


class UnixTimeStampType(Enum):
    '''A unix time stamp type'''
    EPOCHSECONDS = 'epochSeconds'
    EPOCHMILLISECONDS = 'epochMilliseconds'

    def to_api_enum(self) -> api.UnixTimeStampType:
        return api.UnixTimeStampType(self.value)


class OgrSourceTimeFormat:
    '''Base class for OGR time formats'''

    @abstractmethod
    def to_api_dict(self) -> api.OgrSourceTimeFormat:
        pass

    @classmethod
    def seconds(cls, timestamp_type: UnixTimeStampType) -> UnixTimeStampOgrSourceTimeFormat:
        return UnixTimeStampOgrSourceTimeFormat(timestamp_type)

    @classmethod
    def auto(cls) -> AutoOgrSourceTimeFormat:
        return AutoOgrSourceTimeFormat()

    @classmethod
    def custom(cls, format_string: str) -> CustomOgrSourceTimeFormat:
        return CustomOgrSourceTimeFormat(format_string)


@dataclass
class UnixTimeStampOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''An OGR time format specified in seconds (UNIX time)'''
    timestampType: UnixTimeStampType

    def to_api_dict(self) -> api.UnixTimeStampOgrSourceTimeFormat:
        return api.UnixTimeStampOgrSourceTimeFormat({
            "format": "unixTimeStamp",
            "timestampType": self.timestampType.to_api_enum(),
        })


@dataclass
class AutoOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''An auto detection OGR time format'''

    def to_api_dict(self) -> api.OgrSourceTimeFormat:
        return api.OgrSourceTimeFormat({
            "format": "auto"
        })


@dataclass
class CustomOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''A custom OGR time format'''

    custom_format: str

    def to_api_dict(self) -> api.CustomOgrSourceTimeFormat:
        return api.CustomOgrSourceTimeFormat({
            "format": "custom",
            "customFormat": self.custom_format
        })


class OgrSourceDuration():
    '''Base class for the duration part of a OGR time format'''

    @abstractmethod
    def to_api_dict(self) -> api.OgrSourceDurationSpec:
        pass

    @classmethod
    def zero(cls) -> ZeroOgrSourceDurationSpec:
        return ZeroOgrSourceDurationSpec()

    @classmethod
    def infinite(cls) -> InfiniteOgrSourceDurationSpec:
        return InfiniteOgrSourceDurationSpec()

    @classmethod
    def value(
            cls,
            value: int,
            granularity: TimeStepGranularity = TimeStepGranularity.SECONDS) -> ValueOgrSourceDurationSpec:
        '''Returns the value of the duration'''
        return ValueOgrSourceDurationSpec(TimeStep(value, granularity))


class ValueOgrSourceDurationSpec(OgrSourceDuration):
    '''A fixed value for a source duration'''

    step: TimeStep

    def __init__(self, step: TimeStep):
        self.step = step

    def to_api_dict(self) -> api.ValueOgrSourceDurationSpec:
        return api.ValueOgrSourceDurationSpec({
            "type": "value",
            "step": self.step.step,
            "granularity": self.step.granularity.to_api_enum(),
        })


class ZeroOgrSourceDurationSpec(OgrSourceDuration):
    '''An instant, i.e. no duration'''

    def to_api_dict(self) -> api.OgrSourceDurationSpec:
        return api.OgrSourceDurationSpec({
            "type": "zero",
        })


class InfiniteOgrSourceDurationSpec(OgrSourceDuration):
    '''An open-ended time duration'''

    def to_api_dict(self) -> api.OgrSourceDurationSpec:
        return api.OgrSourceDurationSpec({
            "type": "infinite",
        })


class OgrSourceDatasetTimeType:
    '''A time type specification for OGR dataset definitions'''

    @abstractmethod
    def to_api_dict(self) -> api.OgrSourceDatasetTimeType:
        pass

    @classmethod
    def none(cls) -> NoneOgrSourceDatasetTimeType:
        return NoneOgrSourceDatasetTimeType()

    @classmethod
    def start(cls,
              start_field: str,
              start_format: OgrSourceTimeFormat,
              duration: OgrSourceDuration) -> StartOgrSourceDatasetTimeType:
        '''Specify a start column and a fixed duration'''
        return StartOgrSourceDatasetTimeType(start_field, start_format, duration)

    @classmethod
    def start_end(cls,
                  start_field: str,
                  start_format: OgrSourceTimeFormat,
                  end_field: str,
                  end_format: OgrSourceTimeFormat) -> StartEndOgrSourceDatasetTimeType:
        '''The dataset contains start and end column'''
        return StartEndOgrSourceDatasetTimeType(start_field, start_format, end_field, end_format)

    @classmethod
    def start_duration(cls,
                       start_field: str,
                       start_format: OgrSourceTimeFormat,
                       duration_field: str) -> StartDurationOgrSourceDatasetTimeType:
        '''The dataset contains start and a duration column'''
        return StartDurationOgrSourceDatasetTimeType(start_field, start_format, duration_field)


@dataclass
class NoneOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''Specify no time information'''

    def to_api_dict(self) -> api.OgrSourceDatasetTimeType:
        return api.OgrSourceDatasetTimeType({
            "type": "none",
        })


@dataclass
class StartOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''Specify a start column and a fixed duration'''

    start_field: str
    start_format: OgrSourceTimeFormat
    duration: OgrSourceDuration

    def to_api_dict(self) -> api.StartOgrSourceDatasetTimeType:
        return api.StartOgrSourceDatasetTimeType({
            "type": "start",
            "startField": self.start_field,
            "startFormat": self.start_format.to_api_dict(),
            "duration": self.duration.to_api_dict()
        })


@dataclass
class StartEndOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''The dataset contains start and end column'''

    start_field: str
    start_format: OgrSourceTimeFormat
    end_field: str
    end_format: OgrSourceTimeFormat

    def to_api_dict(self) -> api.StartEndOgrSourceDatasetTimeType:
        return api.StartEndOgrSourceDatasetTimeType({
            "type": "start+end",
            "startField": self.start_field,
            "startFormat": self.start_format.to_api_dict(),
            "endField": self.end_field,
            "endFormat": self.end_format.to_api_dict(),
        })


@dataclass
class StartDurationOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''The dataset contains start and a duration column'''

    start_field: str
    start_format: OgrSourceTimeFormat
    duration_field: str

    def to_api_dict(self) -> api.StartDurationOgrSourceDatasetTimeType:
        return api.StartDurationOgrSourceDatasetTimeType({
            "type": "start+duration",
            "startField": self.start_field,
            "startFormat": self.start_format.to_api_dict(),
            "durationField": self.duration_field
        })


class OgrOnError(Enum):
    '''How to handle errors when loading an OGR dataset'''
    IGNORE = "ignore"
    ABORT = "abort"

    def to_api_enum(self) -> api.OgrOnError:
        return api.OgrOnError(self.value)


class DatasetId:
    '''A wrapper for a dataset id'''

    __dataset_id: UUID

    def __init__(self, dataset_id: UUID) -> None:
        self.__dataset_id = dataset_id

    @classmethod
    def from_response(cls, response: api.DatasetId) -> DatasetId:
        '''Parse a http response to an `DatasetId`'''
        if 'error' in response:
            raise GeoEngineException(cast(api.GeoEngineExceptionResponse, response))

        if 'id' not in response:
            raise MissingFieldInResponseException('id', response)

        return DatasetId(UUID(response['id']))

    def __str__(self) -> str:
        return str(self.__dataset_id)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        '''Checks if two dataset ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__dataset_id == other.__dataset_id  # pylint: disable=protected-access

    def to_api_dict(self) -> api.DatasetId:
        return {
            'id': str(self.__dataset_id)
        }


class UploadId:
    '''A wrapper for an upload id'''

    __upload_id: UUID

    def __init__(self, upload_id: UUID) -> None:
        self.__upload_id = upload_id

    @classmethod
    def from_response(cls, response: api.UploadId) -> UploadId:
        '''Parse a http response to an `UploadId`'''
        if 'error' in response:
            raise GeoEngineException(cast(api.GeoEngineExceptionResponse, response))

        if 'id' not in response:  # TODO: improve error handling
            raise MissingFieldInResponseException('id', response)

        return UploadId(UUID(response['id']))

    def __str__(self) -> str:
        return str(self.__upload_id)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        '''Checks if two upload ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__upload_id == other.__upload_id  # pylint: disable=protected-access

    def to_api_dict(self) -> api.UploadId:
        '''Converts the upload id to a dict for the api'''
        return {
            'id': str(self.__upload_id)
        }


class DatasetProperties():
    '''The properties of a dataset'''
    id: Optional[DatasetId]
    name: str
    description: str
    source_operator: Literal['GdalSource', 'OgrSource']  # TODO: add more operators
    symbology: Optional[RasterSymbology]  # TODO: add vector symbology if needed
    provenance: Optional[List[Provenance]]

    def __init__(
        # pylint: disable=too-many-arguments
        self,
        name: str,
        description: str,
        source_operator: Literal['GdalSource', 'OgrSource'] = "GdalSource",
        symbology: Optional[RasterSymbology] = None,
        provenance: Optional[List[Provenance]] = None,
        dataset_id: Optional[DatasetId] = None
    ):
        '''Creates a new `AddDatasetProperties` object'''
        self.dataset_id = dataset_id
        self.name = name
        self.description = description
        self.source_operator = source_operator
        self.symbology = symbology
        self.provenance = provenance

    def to_api_dict(self) -> api.DatasetProperties:
        '''Converts the properties to a dictionary'''
        return {
            'id': str(self.dataset_id) if self.dataset_id is not None else None,
            'name': self.name,
            'description': self.description,
            'sourceOperator': self.source_operator,
            'symbology': self.symbology.to_api_dict() if self.symbology is not None else None,
            'provenance': [p.to_api_dict() for p in self.provenance] if self.provenance is not None else None
        }


class VolumeId:
    '''A wrapper for an volume id'''

    __volume_id: UUID

    def __init__(self, volume_id: UUID) -> None:
        self.__volume_id = volume_id

    @classmethod
    def from_response(cls, response: api.VolumeId) -> VolumeId:
        '''Parse a http response to an `ColumeId`'''
        if 'error' in response:
            raise GeoEngineException(cast(api.GeoEngineExceptionResponse, response))

        if 'id' not in response:  # TODO: improve error handling
            raise MissingFieldInResponseException('id', response)

        return VolumeId(UUID(response['id']))

    def __str__(self) -> str:
        return str(self.__volume_id)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        '''Checks if two volume ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__volume_id == other.__volume_id  # pylint: disable=protected-access

    def to_api_dict(self) -> api.VolumeId:
        '''Converts the volume id to a dictionary containing the id'''
        return {
            'id': str(self.__volume_id)
        }


def pandas_dtype_to_column_type(dtype: np.dtype) -> FeatureDataType:
    '''Convert a pandas `dtype` to a column type'''

    if np.issubdtype(dtype, np.integer):
        return FeatureDataType.INT

    if np.issubdtype(dtype, np.floating):
        return FeatureDataType.FLOAT

    if str(dtype) == 'object':
        return FeatureDataType.TEXT

    raise InputException(
        f'pandas dtype {dtype} has no corresponding column type')


def upload_dataframe(
        df: gpd.GeoDataFrame,
        name: str = "Upload from Python",
        time: OgrSourceDatasetTimeType = OgrSourceDatasetTimeType.none(),
        on_error: OgrOnError = OgrOnError.ABORT,
        timeout: int = 3600) -> DatasetId:
    '''
    Uploads a given dataframe to Geo Engine and returns the id of the created dataset
    '''

    if len(df) == 0:
        raise InputException("Cannot upload empty dataframe")

    if df.crs is None:
        raise InputException("Dataframe must have a specified crs")

    session = get_session()

    df_json = df.to_json()

    response = req.post(f'{session.server_url}/upload',
                        files={"geo.json": df_json},
                        headers=session.auth_header,
                        timeout=timeout).json()

    if 'error' in response:
        raise GeoEngineException(response)

    upload_id = UploadId.from_response(response)

    vector_type = VectorDataType.from_geopandas_type_name(df.geom_type[0])

    columns = {key: VectorColumnInfo(data_type=pandas_dtype_to_column_type(value), measurement=UnitlessMeasurement())
               for (key, value) in df.dtypes.items()
               if str(value) != 'geometry'}

    floats = [key for (key, value) in columns.items() if value.data_type == 'float']
    ints = [key for (key, value) in columns.items() if value.data_type == 'int']
    texts = [key for (key, value) in columns.items() if value.data_type == 'text']

    create = api.CreateDataset({
        'dataPath': api.DatasetPath({
            'upload': str(upload_id)
        }),
        'definition': api.DatasetDefinition({
            'properties': DatasetProperties(
                name=name,
                description='Upload from Python',
                source_operator='OgrSource',
            ).to_api_dict(),
            'metaData': api.OgrMetadata({
                'type': 'OgrMetaData',
                'loadingInfo': api.OgrLoadingInfo({
                    'fileName': 'geo.json',
                    "layerName": 'geo',
                    "dataType": vector_type.to_api_enum(),
                    "time": time.to_api_dict(),
                    "columns": api.OgrLoadingInfoColumns({
                        'y': '',
                        "x": '',
                        "float": floats,
                        "int": ints,
                        "text": texts,
                    }),
                    "onError": on_error.to_api_enum(),

                }),
                'resultDescriptor': VectorResultDescriptor(
                    data_type=vector_type,
                    spatial_reference=df.crs.to_string(),
                    columns=columns,
                ).to_api_dict()
            }),
        })
    })

    response = req.post(f'{session.server_url}/dataset',
                        json=create, headers=session.auth_header,
                        timeout=timeout
                        ).json()

    if 'error' in response:
        raise GeoEngineException(response)

    return DatasetId(response["id"])


class StoredDataset(NamedTuple):
    '''The result of a store dataset request is a combination of `upload_id` and `dataset_id`'''

    dataset_id: DatasetId
    upload_id: UploadId

    @classmethod
    def from_response(cls, response: api.StoredDataset) -> StoredDataset:
        '''Parse a http response to an `StoredDataset`'''
        if 'error' in response:
            raise GeoEngineException(cast(api.GeoEngineExceptionResponse, response))

        if 'dataset' not in response:  # TODO: improve error handling
            raise MissingFieldInResponseException('dataset', response)
        if 'upload' not in response:
            raise MissingFieldInResponseException('upload', response)

        return StoredDataset(
            dataset_id=DatasetId(UUID(response['dataset'])),
            upload_id=UploadId(UUID(response['upload']))
        )

    def to_api_dict(self) -> api.StoredDataset:
        return api.StoredDataset(dataset=str(self.dataset_id), upload=str(self.upload_id))


@dataclass
class Volume:
    '''A volume'''

    name: str
    path: str

    @classmethod
    def from_response(cls, response: api.Volume) -> Volume:
        '''Parse a http response to an `Volume`'''
        return Volume(response['name'], response['path'])

    def to_api_dict(self) -> api.Volume:
        return api.Volume(name=self.name, path=self.path)


def volumes(timeout: int = 60) -> List[Volume]:
    '''Returns a list of all volumes'''

    session = get_session()

    response = req.get(f'{session.server_url}/dataset/volumes',
                       headers=session.admin_auth_header,
                       timeout=timeout
                       ).json()

    return [Volume.from_response(v) for v in response]


def add_dataset(data_store: Union[Volume, UploadId], properties: DatasetProperties, meta_data: api.MetaDataDefinition,
                timeout: int = 60) -> DatasetId:
    '''Adds a dataset to the Geo Engine'''
    dataset_path: api.DatasetStorage
    headers: Dict[str, str]

    session = get_session()

    if isinstance(data_store, Volume):
        headers = session.admin_auth_header
        dataset_path = api.DatasetVolume(
            volume=data_store.name
        )
    else:
        headers = session.auth_header
        dataset_path = api.DatasetPath(
            upload=str(data_store)
        )

    create = api.CreateDataset(

        {
            "dataPath": dataset_path,
            "definition": {
                "properties": properties.to_api_dict(),
                "metaData": meta_data
            }
        })

    data = json.dumps(create, default=dict)

    headers['Content-Type'] = 'application/json'

    response = req.post(f'{session.server_url}/dataset',
                        data=data, headers=headers,
                        timeout=timeout
                        ).json()

    if 'error' in response:
        raise GeoEngineException(response)

    return DatasetId.from_response(response)


def delete_dataset(dataset_id: DatasetId, timeout: int = 60) -> None:
    '''Delete a dataset. The dataset must be owned by the caller.'''

    session = get_session()

    response = req.delete(f'{session.server_url}/dataset/{dataset_id}',
                          headers=session.admin_or_normal_auth_header,
                          timeout=timeout)

    if response.status_code != 200:
        error_json = response.json()
        raise GeoEngineException(error_json)
