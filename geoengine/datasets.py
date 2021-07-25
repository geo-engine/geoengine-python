from __future__ import annotations
from enum import Enum
from attr import dataclass
from geoengine.types import TimeStep, TimeStepGranularity, VectorDataType
from geoengine.auth import get_session
from typing import Dict
from geoengine.error import GeoEngineException, InputException
from uuid import UUID
import geopandas as gpd
import requests as req
import numpy as np


class DatasetId:
    def __init__():
        pass


class InternalDatasetId(DatasetId):
    __dataset_id: UUID

    def __init__(self, dataset_id: UUID):
        self.__dataset_id = dataset_id

    @classmethod
    def from_response(self, response: Dict[str, str]) -> InternalDatasetId:
        if not 'id' in response or not 'type' in response['id'] or response['id']['type'] != 'internal':
            raise GeoEngineException(response)

        return InternalDatasetId(response['id']['datasetId'])

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "internal",
            "datasetId": self.__dataset_id
        }

    def __str__(self) -> str:
        return str(self.__dataset_id)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dataset_id == other.__dataset_id
        else:
            return False


class UploadId:
    __id: UUID

    def __init__(self, id: UUID) -> None:
        self.__id = id

    @classmethod
    def from_response(self, response: Dict[str, str]) -> UploadId:
        if not 'id' in response:
            raise GeoEngineException(response)

        return UploadId(response['id'])

    def __str__(self) -> str:
        return self.__id

    def __repr__(self) -> str:
        return str(self)


class OgrSourceTimeFormat:
    def to_dict(self) -> Dict[str, str]:
        pass

    @classmethod
    def seconds(cls) -> SecondsOgrSourceTimeFormat:
        return SecondsOgrSourceTimeFormat()

    @classmethod
    def auto(cls) -> AutoOgrSourceTimeFormat:
        return AutoOgrSourceTimeFormat()

    @classmethod
    def custom(cls, format: str) -> CustomOgrSourceTimeFormat:
        return CustomOgrSourceTimeFormat(format)


@dataclass
class SecondsOgrSourceTimeFormat(OgrSourceTimeFormat):
    def to_dict(self) -> Dict[str, str]:
        return {
            "format": "seconds"
        }


@dataclass
class AutoOgrSourceTimeFormat(OgrSourceTimeFormat):
    def to_dict(self) -> Dict[str, str]:
        return {
            "format": "auto"
        }


@dataclass
class CustomOgrSourceTimeFormat(OgrSourceTimeFormat):
    custom: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "format": "custom",
            "customFormat": self.custom
        }


class OgrSourceDuration:
    def to_dict(self) -> Dict[str, str]:
        pass

    @classmethod
    def zero(cls) -> OgrSourceTimeFormat:
        return ZeroOgrSourceDurationSpec()

    @classmethod
    def infinite(cls) -> OgrSourceTimeFormat:
        return InfiniteOgrSourceDurationSpec()

    @classmethod
    def value(cls, value: int, granularity: TimeStepGranularity = TimeStepGranularity.seconds) -> OgrSourceTimeFormat:
        return ValueOgrSourceDurationSpec(TimeStep(value, granularity))


@dataclass
class ValueOgrSourceDurationSpec(OgrSourceDuration):
    step: TimeStep

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "value",
            "step": self.step.step,
            "granularity": self.step.granularity.value
        }


@dataclass
class ZeroOgrSourceDurationSpec(OgrSourceDuration):
    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "zero",
        }


@dataclass
class InfiniteOgrSourceDurationSpec(OgrSourceDuration):
    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "infinite",
        }


class OgrSourceDatasetTimeType:
    def to_dict(self) -> Dict[str, str]:
        pass

    @classmethod
    def none(cls) -> OgrSourceTimeFormat:
        return NoneOgrSourceDatasetTimeType()

    @classmethod
    def start(cls, start_field: str, start_format: OgrSourceTimeFormat, duration: OgrSourceDuration) -> OgrSourceTimeFormat:
        return StartOgrSourceDatasetTimeType(start_field, start_format, duration)

    @classmethod
    def start_end(cls, start_field: str, start_format: OgrSourceTimeFormat, end_field: str, end_format: OgrSourceTimeFormat) -> OgrSourceTimeFormat:
        return StartEndOgrSourceDatasetTimeType(start_field, start_format, end_field, end_format)

    @classmethod
    def start_duration(cls, start_field: str, start_format: OgrSourceTimeFormat, duration_field: str) -> OgrSourceTimeFormat:
        return StartEndOgrSourceDatasetTimeType(start_field, start_format, duration_field)


@dataclass
class NoneOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    def to_dict(self) -> Dict[str, str]:
        return {
            "type": "none",
        }


@dataclass
class StartOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
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
    ignore = "ignore"
    abort = "abort"


def pandas_dtype_to_column_type(dtype: np.dtype) -> str:
    if np.issubdtype(dtype, np.integer):
        return 'int'

    if np.issubdtype(dtype, np.floating):
        return 'float'

    if str(dtype) == 'object':
        return 'text'

    raise InputException(
        f'pandas dtype {dtype} has no corresponding column type')


def upload_dataframe(df: gpd.GeoDataFrame, name: str = "Upload from Python", time: OgrSourceDatasetTimeType = OgrSourceDatasetTimeType.none(), onError: OgrOnError = OgrOnError.abort) -> DatasetId:
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

    vectorType = VectorDataType.from_geopandas_type_name(df.geom_type[0])

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
                    "dataType": vectorType.value,
                    "time": time.to_dict(),
                    "columns": {
                        "x": "",
                        "float": floats,
                        "int": ints,
                        "text": texts
                    },
                    "onError": onError.value
                },
                "resultDescriptor": {
                    "type": "vector",
                    "dataType": vectorType.value,
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

    return InternalDatasetId.from_response(response)
