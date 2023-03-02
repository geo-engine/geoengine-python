'''Entry point for Geo Engine Python Library'''

from pkg_resources import get_distribution
from requests import utils

from .auth import Session, get_session, initialize, reset
from .colorizer import Colorizer, ColorBreakpoint, LinearGradientColorizer, PaletteColorizer, \
    LogarithmicGradientColorizer
from .datasets import upload_dataframe, StoredDataset, add_public_raster_dataset, volumes, DatasetProperties, \
    delete_dataset
from .error import GeoEngineException, InputException, UninitializedException, TypeException, \
    MethodNotCalledOnPlotException, MethodNotCalledOnRasterException, MethodNotCalledOnVectorException, \
    SpatialReferenceMismatchException, check_response_for_error, ModificationNotOnLayerDbException, \
    NoAdminSessionException, InvalidUrlException, MissingFieldInResponseException
from .layers import Layer, LayerCollection, LayerListing, LayerCollectionListing, \
    LayerId, LayerCollectionId, LayerProviderId, \
    layer_collection, layer
from .types import QueryRectangle,  \
    RasterResultDescriptor, Provenance, UnitlessMeasurement, ContinuousMeasurement, \
    ClassificationMeasurement, BoundingBox2D, TimeInterval, SpatialResolution, SpatialPartition2D, \
    RasterSymbology, VectorSymbology, VectorDataType, VectorResultDescriptor, VectorColumnInfo, \
    DEFAULT_ISO_TIME_FORMAT

from .workflow import WorkflowId, Workflow, workflow_by_id, register_workflow, get_quota, update_quota

from . import workflow_operators


DEFAULT_USER_AGENT = f'geoengine-python/{get_distribution("geoengine").version}'


def default_user_agent(_name="python-requests"):
    return DEFAULT_USER_AGENT


utils.default_user_agent = default_user_agent
