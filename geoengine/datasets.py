'''
Module for working with datasets and source definitions
'''

from __future__ import annotations
from typing import Dict

from enum import Enum
from uuid import UUID

from attr import dataclass
import numpy as np
import geopandas as gpd
import requests as req

from geoengine.error import GeoEngineException, InputException
from geoengine.auth import get_session
from geoengine.types import TimeStep, TimeStepGranularity, DatasetId, VectorDataType, InternalDatasetId


class OgrSourceTimeFormat:
    '''Base class for OGR time formats'''

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

    custom: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "format": "custom",
            "customFormat": self.custom
        }


class OgrSourceDuration:
    '''Base class for the duration part of a OGR time format'''

    def to_dict(self) -> Dict[str, str]:
        pass

    @classmethod
    def zero(cls) -> OgrSourceTimeFormat:
        return ZeroOgrSourceDurationSpec()

    @classmethod
    def infinite(cls) -> OgrSourceTimeFormat:
        return InfiniteOgrSourceDurationSpec()

    @classmethod
    def value(cls, value: int, granularity: TimeStepGranularity = TimeStepGranularity.SECONDS) -> OgrSourceTimeFormat:
        return ValueOgrSourceDurationSpec(TimeStep(value, granularity))


@dataclass
class ValueOgrSourceDurationSpec(OgrSourceDuration):
    '''A fixed value for a source duration'''

    step: TimeStep

    def to_dict(self) -> Dict[str, str]:
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

    def to_dict(self) -> Dict[str, str]:
        pass

    @classmethod
    def none(cls) -> OgrSourceTimeFormat:
        return NoneOgrSourceDatasetTimeType()

    @classmethod
    def start(cls,
              start_field: str,
              start_format: OgrSourceTimeFormat,
              duration: OgrSourceDuration) -> OgrSourceTimeFormat:
        '''Specify a start column and a fixed duration'''
        return StartOgrSourceDatasetTimeType(start_field, start_format, duration)

    @classmethod
    def start_end(cls,
                  start_field: str,
                  start_format: OgrSourceTimeFormat,
                  end_field: str,
                  end_format: OgrSourceTimeFormat) -> OgrSourceTimeFormat:
        '''The dataset contains start and end column'''
        return StartEndOgrSourceDatasetTimeType(start_field, start_format, end_field, end_format)

    @classmethod
    def start_duration(cls,
                       start_field: str,
                       start_format: OgrSourceTimeFormat,
                       duration_field: str) -> OgrSourceTimeFormat:
        '''The dataset contains start and a duration column'''
        return StartEndOgrSourceDatasetTimeType(start_field, start_format, duration_field)


@dataclass
class NoneOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''Specify no time information'''

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "none",
        }


@dataclass
class StartOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''Specify a start column and a fixed duration'''

    start_field: str
    start_format: OgrSourceTimeFormat
    duration: OgrSourceDuration

    def to_dict(self) -> Dict[str, str]:
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

    def to_dict(self) -> Dict[str, str]:
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

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "start+duration",
            "startField": self.start_field,
            "startFormat": self.start_format.to_dict(),
            "durationField": self.duration_field
        }


class OgrOnError(Enum):
    IGNORE = "ignore"
    ABORT = "abort"


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

        return UploadId(response['id'])

    def __str__(self) -> str:
        return self.__upload_id

    def __repr__(self) -> str:
        return str(self)


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
        on_error: OgrOnError = OgrOnError.ABORT) -> DatasetId:
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
                        files={"geo.json": df_json}, headers=session.auth_header).json()

    if 'error' in response:
        raise GeoEngineException(response)

    upload_id = UploadId.from_response(response)

    vector_type = VectorDataType.from_geopandas_type_name(df.geom_type[0])

    columns = {key: pandas_dtype_to_column_type(value) for (key, value) in df.dtypes.items()
               if str(value) != 'geometry'}

    floats = [key for (key, value) in columns.items() if value == 'float']
    ints = [key for (key, value) in columns.items() if value == 'int']
    texts = [key for (key, value) in columns.items() if value == 'text']

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
                        json=create, headers=session.auth_header).json()

    if 'error' in response:
        raise GeoEngineException(response)

    return InternalDatasetId.from_response(response["id"])
