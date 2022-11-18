'''
Module for working with datasets and source definitions
'''

from __future__ import annotations
from abc import abstractmethod
from typing import Dict, NamedTuple, Union, Generic, TypeVar


from enum import Enum
from uuid import UUID

from attr import dataclass
import numpy as np
import geopandas as gpd
import requests as req

from geoengine.error import GeoEngineException, InputException
from geoengine.auth import get_session
from geoengine.types import TimeStep, TimeStepGranularity, VectorDataType


_OrgSourceDurationDictT = TypeVar('_OrgSourceDurationDictT', str, Union[str, int, TimeStepGranularity])


class OgrSourceTimeFormat:
    '''Base class for OGR time formats'''

    @abstractmethod
    def to_dict(self) -> Dict[str, str]:
        pass

    @classmethod
    def seconds(cls) -> SecondsOgrSourceTimeFormat:
        return SecondsOgrSourceTimeFormat()

    @classmethod
    def auto(cls) -> AutoOgrSourceTimeFormat:
        return AutoOgrSourceTimeFormat()

    @classmethod
    def custom(cls, format_string: str) -> CustomOgrSourceTimeFormat:
        return CustomOgrSourceTimeFormat(format_string)


@dataclass
class SecondsOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''An OGR time format specified in seconds (UNIX time)'''

    def to_dict(self) -> Dict[str, str]:
        return {
            "format": "seconds"
        }


@dataclass
class AutoOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''An auto detection OGR time format'''

    def to_dict(self) -> Dict[str, str]:
        return {
            "format": "auto"
        }


@dataclass
class CustomOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''A custom OGR time format'''

    custom_format: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "format": "custom",
            "customFormat": self.custom_format
        }


class OgrSourceDuration(Generic[_OrgSourceDurationDictT]):
    '''Base class for the duration part of a OGR time format'''

    @abstractmethod
    def to_dict(self) -> Dict[str, _OrgSourceDurationDictT]:
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


@dataclass
class ValueOgrSourceDurationSpec(OgrSourceDuration):
    '''A fixed value for a source duration'''

    step: TimeStep

    def to_dict(self) -> Dict[str, Union[str, int, TimeStepGranularity]]:
        return {
            "type": "value",
            "step": self.step.step,
            "granularity": self.step.granularity.value
        }


@dataclass
class ZeroOgrSourceDurationSpec(OgrSourceDuration):
    '''An instant, i.e. no duration'''

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "zero",
        }


@dataclass
class InfiniteOgrSourceDurationSpec(OgrSourceDuration):
    '''An open-ended time duration'''

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "infinite",
        }


class OgrSourceDatasetTimeType:
    '''A time type specification for OGR dataset definitions'''

    @abstractmethod
    def to_dict(self) -> Dict[str, Union[str, Dict[str, str]]]:
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

    def to_dict(self) -> Dict[str, Union[str, Dict[str, str]]]:
        return {
            "type": "none",
        }


@dataclass
class StartOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''Specify a start column and a fixed duration'''

    start_field: str
    start_format: OgrSourceTimeFormat
    duration: OgrSourceDuration

    def to_dict(self) -> Dict[str, Union[str, Dict[str, str]]]:
        return {
            "type": "start",
            "startField": self.start_field,
            "startFormat": self.start_format.to_dict(),
            "duration": self.duration.to_dict()
        }


@dataclass
class StartEndOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''The dataset contains start and end column'''

    start_field: str
    start_format: OgrSourceTimeFormat
    end_field: str
    end_format: OgrSourceTimeFormat

    def to_dict(self) -> Dict[str, Union[str, Dict[str, str]]]:
        return {
            "type": "start+end",
            "startField": self.start_field,
            "startFormat": self.start_format.to_dict(),
            "endField": self.end_field,
            "endFormat": self.end_format.to_dict(),
        }


@dataclass
class StartDurationOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''The dataset contains start and a duration column'''

    start_field: str
    start_format: OgrSourceTimeFormat
    duration_field: str

    def to_dict(self) -> Dict[str, Union[str, Dict[str, str]]]:
        return {
            "type": "start+duration",
            "startField": self.start_field,
            "startFormat": self.start_format.to_dict(),
            "durationField": self.duration_field
        }


class OgrOnError(Enum):
    IGNORE = "ignore"
    ABORT = "abort"


class DatasetId:
    '''A wrapper for a dataset id'''

    __dataset_id: UUID

    def __init__(self, dataset_id: UUID) -> None:
        self.__dataset_id = dataset_id

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> DatasetId:
        '''Parse a http response to an `DatasetId`'''
        if 'id' not in response:
            raise GeoEngineException(response)

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


class UploadId:
    '''A wrapper for an upload id'''

    __upload_id: UUID

    def __init__(self, upload_id: UUID) -> None:
        self.__upload_id = upload_id

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> UploadId:
        '''Parse a http response to an `UploadId`'''
        if 'id' not in response:
            raise GeoEngineException(response)

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


def pandas_dtype_to_column_type(dtype: np.dtype) -> str:
    '''Convert a pandas `dtype` to a column type'''

    if np.issubdtype(dtype, np.integer):
        return 'int'

    if np.issubdtype(dtype, np.floating):
        return 'float'

    if str(dtype) == 'object':
        return 'text'

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

    columns = {key: {'dataType': pandas_dtype_to_column_type(value), 'measurement': {'type': 'unitless'}}
               for (key, value) in df.dtypes.items()
               if str(value) != 'geometry'}

    floats = [key for (key, value) in columns.items() if value['dataType'] == 'float']
    ints = [key for (key, value) in columns.items() if value['dataType'] == 'int']
    texts = [key for (key, value) in columns.items() if value['dataType'] == 'text']

    create = {
        "upload": str(upload_id),
        "definition": {
            "properties": {
                "name": name,
                "description": "",
                "sourceOperator": "OgrSource"
            },
            "metaData": {
                "type": "OgrMetaData",
                "loadingInfo": {
                    "fileName": "geo.json",
                    "layerName": "geo",
                    "dataType": vector_type.value,
                    "time": time.to_dict(),
                    "columns": {
                        "x": "",
                        "float": floats,
                        "int": ints,
                        "text": texts
                    },
                    "onError": on_error.value
                },
                "resultDescriptor": {
                    "type": "vector",
                    "dataType": vector_type.value,
                    "columns": columns,
                    "spatialReference": df.crs.to_string()
                }
            }
        }
    }

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
    def from_response(cls, response: Dict[str, str]) -> StoredDataset:
        '''Parse a http response to an `StoredDataset`'''
        if 'dataset' not in response and 'upload' not in response:
            raise GeoEngineException(response)

        return StoredDataset(
            dataset_id=DatasetId(UUID(response['dataset'])),
            upload_id=UploadId(UUID(response['upload']))
        )
