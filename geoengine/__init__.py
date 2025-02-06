'''Entry point for Geo Engine Python Library'''

from pkg_resources import get_distribution
from requests import utils
from pydantic import ValidationError
from geoengine_openapi_client.exceptions import BadRequestException, OpenApiException, ApiTypeError, ApiValueError, \
    ApiKeyError, ApiAttributeError, ApiException, NotFoundException
from geoengine_openapi_client import UsageSummaryGranularity

from . import workflow_builder
from .raster_workflow_rio_writer import RasterWorkflowRioWriter
from .raster import RasterTile2D
from .workflow import WorkflowId, Workflow, workflow_by_id, register_workflow, get_quota, update_quota, data_usage, \
    data_usage_summary
from .util import clamp_datetime_ms_ns
from .resource_identifier import LAYER_DB_PROVIDER_ID, LAYER_DB_ROOT_COLLECTION_ID, DatasetName, UploadId, \
    LayerId, LayerCollectionId, LayerProviderId, Resource, MlModelName
from .types import QueryRectangle, GeoTransform, \
    RasterResultDescriptor, Provenance, UnitlessMeasurement, ContinuousMeasurement, \
    ClassificationMeasurement, BoundingBox2D, TimeInterval, SpatialResolution, SpatialPartition2D, \
    RasterSymbology, VectorSymbology, VectorDataType, VectorResultDescriptor, VectorColumnInfo, \
    FeatureDataType, RasterBandDescriptor, DEFAULT_ISO_TIME_FORMAT, RasterColorizer, SingleBandRasterColorizer, \
    MultiBandRasterColorizer
from .tasks import Task, TaskId
from .permissions import add_permission, remove_permission, add_role, remove_role, assign_role, revoke_role, \
    ADMIN_ROLE_ID, REGISTERED_USER_ROLE_ID, ANONYMOUS_USER_ROLE_ID, Permission, UserId, RoleId
from .ml import register_ml_model, MlModelConfig
from .layers import Layer, LayerCollection, LayerListing, LayerCollectionListing, \
    layer_collection, layer
from .error import GeoEngineException, InputException, UninitializedException, TypeException, \
    MethodNotCalledOnPlotException, MethodNotCalledOnRasterException, MethodNotCalledOnVectorException, \
    SpatialReferenceMismatchException, check_response_for_error, ModificationNotOnLayerDbException, \
    InvalidUrlException, MissingFieldInResponseException, OGCXMLError
from .auth import Session, get_session, initialize, reset
from .colorizer import Colorizer, ColorBreakpoint, LinearGradientColorizer, PaletteColorizer, \
    LogarithmicGradientColorizer
from .datasets import upload_dataframe, StoredDataset, add_dataset, volumes, AddDatasetProperties, \
    delete_dataset, list_datasets, DatasetListOrder, OgrSourceDatasetTimeType, OgrOnError, \
    add_or_replace_dataset_with_permissions, dataset_info_by_name


DEFAULT_USER_AGENT = f'geoengine-python/{get_distribution("geoengine").version}'


def default_user_agent(_name="python-requests"):
    return DEFAULT_USER_AGENT


utils.default_user_agent = default_user_agent
