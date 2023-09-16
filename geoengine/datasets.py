'''
Module for working with datasets and source definitions
'''

from __future__ import annotations
from abc import abstractmethod
from typing import List, NamedTuple, Optional, Union, Literal
from enum import Enum
from uuid import UUID
from attr import dataclass
import numpy as np
import geopandas as gpd
import openapi_client
from geoengine import api
from geoengine.error import InputException, MissingFieldInResponseException
from geoengine.auth import get_session
from geoengine.types import Provenance, RasterSymbology, TimeStep, \
    TimeStepGranularity, VectorDataType, VectorResultDescriptor, VectorColumnInfo, \
    UnitlessMeasurement, FeatureDataType


class UnixTimeStampType(Enum):
    '''A unix time stamp type'''
    EPOCHSECONDS = 'epochSeconds'
    EPOCHMILLISECONDS = 'epochMilliseconds'

    def to_api_enum(self) -> openapi_client.UnixTimeStampType:
        return openapi_client.UnixTimeStampType(self.value)


class OgrSourceTimeFormat:
    '''Base class for OGR time formats'''

    @abstractmethod
    def to_api_dict(self) -> openapi_client.OgrSourceTimeFormat:
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

    def to_api_dict(self) -> openapi_client.OgrSourceTimeFormat:
        return openapi_client.OgrSourceTimeFormat(openapi_client.UnixTimeStampOgrSourceTimeFormat(
            format="unixTimeStamp",
            timestamp_type=self.timestampType.to_api_enum(),
        ))


@dataclass
class AutoOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''An auto detection OGR time format'''

    def to_api_dict(self) -> openapi_client.OgrSourceTimeFormat:
        return openapi_client.OgrSourceTimeFormat(openapi_client.AutoOgrSourceTimeFormat(
            format="auto"
        ))


@dataclass
class CustomOgrSourceTimeFormat(OgrSourceTimeFormat):
    '''A custom OGR time format'''

    custom_format: str

    def to_api_dict(self) -> openapi_client.OgrSourceTimeFormat:
        return openapi_client.OgrSourceTimeFormat(openapi_client.CustomOgrSourceTimeFormat(
            format="custom",
            custom_format=self.custom_format
        ))


class OgrSourceDuration():
    '''Base class for the duration part of a OGR time format'''

    @abstractmethod
    def to_api_dict(self) -> openapi_client.OgrSourceDurationSpec:
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

    def to_api_dict(self) -> openapi_client.OgrSourceDurationSpec:
        return openapi_client.OgrSourceDurationSpec(openapi_client.TimeStepWithType(
            type="value",
            step=self.step.step,
            granularity=self.step.granularity.to_api_enum(),
        ))


class ZeroOgrSourceDurationSpec(OgrSourceDuration):
    '''An instant, i.e. no duration'''

    def to_api_dict(self) -> openapi_client.OgrSourceDurationSpec:
        return openapi_client.OgrSourceDurationSpec(openapi_client.ZeroOgrSourceDurationSpec(
            type="zero",
        ))


class InfiniteOgrSourceDurationSpec(OgrSourceDuration):
    '''An open-ended time duration'''

    def to_api_dict(self) -> openapi_client.OgrSourceDurationSpec:
        return openapi_client.OgrSourceDurationSpec(openapi_client.InfiniteOgrSourceDurationSpec(
            type="infinite",
        ))


class OgrSourceDatasetTimeType:
    '''A time type specification for OGR dataset definitions'''

    @abstractmethod
    def to_api_dict(self) -> openapi_client.OgrSourceDatasetTimeType:
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

    def to_api_dict(self) -> openapi_client.OgrSourceDatasetTimeType:
        return openapi_client.OgrSourceDatasetTimeType(openapi_client.NoneOgrSourceDatasetTimeType(
            type="none",
        ))


@dataclass
class StartOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''Specify a start column and a fixed duration'''

    start_field: str
    start_format: OgrSourceTimeFormat
    duration: OgrSourceDuration

    def to_api_dict(self) -> openapi_client.OgrSourceDatasetTimeType:
        return openapi_client.OgrSourceDatasetTimeType(openapi_client.StartOgrSourceDatasetTimeType(
            type="start",
            start_field=self.start_field,
            start_format=self.start_format.to_api_dict(),
            duration=self.duration.to_api_dict()
        ))


@dataclass
class StartEndOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''The dataset contains start and end column'''

    start_field: str
    start_format: OgrSourceTimeFormat
    end_field: str
    end_format: OgrSourceTimeFormat

    def to_api_dict(self) -> openapi_client.OgrSourceDatasetTimeType:
        return openapi_client.OgrSourceDatasetTimeType(openapi_client.StartEndOgrSourceDatasetTimeType(
            type="startEnd",
            start_field=self.start_field,
            start_format=self.start_format.to_api_dict(),
            end_field=self.end_field,
            end_format=self.end_format.to_api_dict(),
        ))


@dataclass
class StartDurationOgrSourceDatasetTimeType(OgrSourceDatasetTimeType):
    '''The dataset contains start and a duration column'''

    start_field: str
    start_format: OgrSourceTimeFormat
    duration_field: str

    def to_api_dict(self) -> openapi_client.OgrSourceDatasetTimeType:
        return openapi_client.OgrSourceDatasetTimeType(openapi_client.StartDurationOgrSourceDatasetTimeType(
            type="startDuration",
            start_field=self.start_field,
            start_format=self.start_format.to_api_dict(),
            duration_field=self.duration_field
        ))


class OgrOnError(Enum):
    '''How to handle errors when loading an OGR dataset'''
    IGNORE = "ignore"
    ABORT = "abort"

    def to_api_enum(self) -> openapi_client.OgrSourceErrorSpec:
        return openapi_client.OgrSourceErrorSpec(self.value)


class DatasetName:
    '''A wrapper for a dataset id'''

    __dataset_name: str

    def __init__(self, dataset_name: str) -> None:
        self.__dataset_name = dataset_name

    @classmethod
    def from_response(cls, response: openapi_client.CreateDatasetHandler200Response) -> DatasetName:
        '''Parse a http response to an `DatasetId`'''
        return DatasetName(response.dataset_name)

    def __str__(self) -> str:
        return self.__dataset_name

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        '''Checks if two dataset ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__dataset_name == other.__dataset_name  # pylint: disable=protected-access

    def to_api_dict(self) -> openapi_client.CreateDatasetHandler200Response:
        return openapi_client.CreateDatasetHandler200Response(
            dataset_name=str(self.__dataset_name)
        )


class UploadId:
    '''A wrapper for an upload id'''

    __upload_id: UUID

    def __init__(self, upload_id: UUID) -> None:
        self.__upload_id = upload_id

    @classmethod
    def from_response(cls, response: openapi_client.AddCollection200Response) -> UploadId:
        '''Parse a http response to an `UploadId`'''
        return UploadId(UUID(response.id))

    def __str__(self) -> str:
        return str(self.__upload_id)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        '''Checks if two upload ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__upload_id == other.__upload_id  # pylint: disable=protected-access

    def to_api_dict(self) -> openapi_client.AddCollection200Response:
        '''Converts the upload id to a dict for the api'''
        return openapi_client.AddCollection200Response(
            id=str(self.__upload_id)
        )


class AddDatasetProperties():
    '''The properties for adding a dataset'''
    name: Optional[str]
    display_name: str
    description: str
    source_operator: Literal['GdalSource', 'OgrSource']  # TODO: add more operators
    symbology: Optional[RasterSymbology]  # TODO: add vector symbology if needed
    provenance: Optional[List[Provenance]]

    def __init__(
        # pylint: disable=too-many-arguments
        self,
        display_name: str,
        description: str,
        source_operator: Literal['GdalSource', 'OgrSource'] = "GdalSource",
        symbology: Optional[RasterSymbology] = None,
        provenance: Optional[List[Provenance]] = None,
        name: Optional[str] = None
    ):
        '''Creates a new `AddDatasetProperties` object'''
        self.name = name
        self.display_name = display_name
        self.description = description
        self.source_operator = source_operator
        self.symbology = symbology
        self.provenance = provenance

    def to_api_dict(self) -> openapi_client.AddDataset:
        '''Converts the properties to a dictionary'''
        return openapi_client.AddDataset(
            name=str(self.name) if self.name is not None else None,
            display_name=self.display_name,
            description=self.description,
            source_operator=self.source_operator,
            symbology=self.symbology.to_api_dict() if self.symbology is not None else None,
            provenance=[p.to_api_dict() for p in self.provenance] if self.provenance is not None else None
        )


class VolumeId:
    '''A wrapper for an volume id'''

    __volume_id: UUID

    def __init__(self, volume_id: UUID) -> None:
        self.__volume_id = volume_id

    def __str__(self) -> str:
        return str(self.__volume_id)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        '''Checks if two volume ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__volume_id == other.__volume_id  # pylint: disable=protected-access


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
        display_name: str = "Upload from Python",
        name: Optional[str] = None,
        time: OgrSourceDatasetTimeType = OgrSourceDatasetTimeType.none(),
        on_error: OgrOnError = OgrOnError.ABORT,
        timeout: int = 3600) -> DatasetName:
    """
    Uploads a given dataframe to Geo Engine.

    Parameters
    ----------
    df
        The dataframe to upload.
    display_name
        The display name of the dataset. Defaults to "Upload from Python".
    name
        The name the dataset should have. If not given, a random name (UUID) will be generated.
    time
        A time configuration for the dataset. Defaults to `OgrSourceDatasetTimeType.none()`.
    on_error
        The error handling strategy. Defaults to `OgrOnError.ABORT`.
    timeout
        The upload timeout in seconds. Defaults to 3600.

    Returns
    -------
    DatasetName
        The name of the uploaded dataset

    Raises
    ------
    GeoEngineException
        If the dataset could not be uploaded or the name is already taken.
    """
    # pylint: disable=too-many-arguments,too-many-locals

    if len(df) == 0:
        raise InputException("Cannot upload empty dataframe")

    if df.crs is None:
        raise InputException("Dataframe must have a specified crs")

    session = get_session()

    df_json = df.to_json()

    with openapi_client.ApiClient(session.configuration) as api_client:
        uploads_api = openapi_client.UploadsApi(api_client)
        response = uploads_api.upload_handler({"geo.json": df_json}, _request_timeout=timeout)

    upload_id = UploadId.from_response(response)

    vector_type = VectorDataType.from_geopandas_type_name(df.geom_type[0])

    columns = {key: VectorColumnInfo(data_type=pandas_dtype_to_column_type(value), measurement=UnitlessMeasurement())
               for (key, value) in df.dtypes.items()
               if str(value) != 'geometry'}

    floats = [key for (key, value) in columns.items() if value.data_type == 'float']
    ints = [key for (key, value) in columns.items() if value.data_type == 'int']
    texts = [key for (key, value) in columns.items() if value.data_type == 'text']

    create = openapi_client.CreateDataset(
        data_path=openapi_client.DataPath(openapi_client.DataPathOneOf1(
            upload=str(upload_id)
        )),
        definition=openapi_client.DatasetDefinition(
            properties=AddDatasetProperties(
                display_name=display_name,
                name=name,
                description='Upload from Python',
                source_operator='OgrSource',
            ).to_api_dict(),
            meta_data=openapi_client.MetaDataDefinition(openapi_client.OgrMetaDataWithType(
                type='OgrMetaData',
                loading_info=openapi_client.OgrSourceDataset(
                    file_name='geo.json',
                    layer_name='geo',
                    data_type=vector_type.to_api_enum(),
                    time=time.to_api_dict(),
                    columns=openapi_client.OgrSourceColumnSpec(
                        y='',
                        x='',
                        float=floats,
                        int=ints,
                        text=texts,
                    ),
                    on_error=on_error.to_api_enum(),
                ),
                result_descriptor=VectorResultDescriptor(
                    data_type=vector_type,
                    spatial_reference=df.crs.to_string(),
                    columns=columns,
                ).to_api_dict()
            )),
        )
    )

    with openapi_client.ApiClient(session.configuration) as api_client:
        datasets_api = openapi_client.DatasetsApi(api_client)
        response2 = datasets_api.create_dataset_handler(create, _request_timeout=timeout)

    return DatasetName.from_response(response2)


class StoredDataset(NamedTuple):
    '''The result of a store dataset request is a combination of `upload_id` and `dataset_name`'''

    dataset_name: DatasetName
    upload_id: UploadId

    @classmethod
    def from_response(cls, response: api.StoredDataset) -> StoredDataset:
        '''Parse a http response to an `StoredDataset`'''

        if 'dataset' not in response:  # TODO: improve error handling
            raise MissingFieldInResponseException('dataset', response)
        if 'upload' not in response:
            raise MissingFieldInResponseException('upload', response)

        return StoredDataset(
            dataset_name=DatasetName(response['dataset']),
            upload_id=UploadId(UUID(response['upload']))
        )

    def to_api_dict(self) -> api.StoredDataset:
        return api.StoredDataset(dataset=str(self.dataset_name), upload=str(self.upload_id))


@dataclass
class Volume:
    '''A volume'''

    name: str
    path: str

    @classmethod
    def from_response(cls, response: openapi_client.Volume) -> Volume:
        '''Parse a http response to an `Volume`'''
        return Volume(response.name, response.path)

    def to_api_dict(self) -> openapi_client.Volume:
        return openapi_client.Volume(name=self.name, path=self.path)


def volumes(timeout: int = 60) -> List[Volume]:
    '''Returns a list of all volumes'''

    session = get_session()

    with openapi_client.ApiClient(session.configuration) as api_client:
        datasets_api = openapi_client.DatasetsApi(api_client)
        response = datasets_api.list_volumes_handler(_request_timeout=timeout)

    return [Volume.from_response(v) for v in response]


def add_dataset(data_store: Union[Volume, UploadId],
                properties: AddDatasetProperties,
                meta_data: openapi_client.MetaDataDefinition,
                timeout: int = 60) -> DatasetName:
    '''Adds a dataset to the Geo Engine'''

    if isinstance(data_store, Volume):
        dataset_path = openapi_client.DataPath(openapi_client.DataPathOneOf(
            volume=data_store.name
        ))
    else:
        dataset_path = openapi_client.DataPath(openapi_client.DataPathOneOf1(
            upload=str(data_store)
        ))

    create = openapi_client.CreateDataset(
        data_path=dataset_path,
        definition=openapi_client.DatasetDefinition(
            properties=properties.to_api_dict(),
            meta_data=meta_data
        )
    )

    session = get_session()

    with openapi_client.ApiClient(session.configuration) as api_client:
        datasets_api = openapi_client.DatasetsApi(api_client)
        response = datasets_api.create_dataset_handler(create, _request_timeout=timeout)

    return DatasetName.from_response(response)


def delete_dataset(dataset_name: DatasetName, timeout: int = 60) -> None:
    '''Delete a dataset. The dataset must be owned by the caller.'''

    session = get_session()

    with openapi_client.ApiClient(session.configuration) as api_client:
        datasets_api = openapi_client.DatasetsApi(api_client)
        datasets_api.delete_dataset_handler(str(dataset_name), _request_timeout=timeout)


class DatasetListOrder(Enum):
    NAME_ASC = 'NameAsc'
    NAME_DESC = 'NameDesc'


def list_datasets(offset: int = 0,
                  limit: int = 20,
                  order: DatasetListOrder = DatasetListOrder.NAME_ASC,
                  name_filter: Optional[str] = None,
                  timeout: int = 60) -> List[openapi_client.DatasetListing]:
    '''List datasets'''

    session = get_session()

    with openapi_client.ApiClient(session.configuration) as api_client:
        datasets_api = openapi_client.DatasetsApi(api_client)
        response = datasets_api.list_datasets_handler(
            offset=offset,
            limit=limit,
            order=openapi_client.OrderBy(order.value),
            filter=name_filter,
            _request_timeout=timeout
        )

    return response
