'''Entry point for Geo Engine Python Library'''

from pkg_resources import get_distribution
from requests import utils

from .auth import Session, get_session, initialize, reset
from .colorizer import Colorizer
from .datasets import upload_dataframe, StoredDataset
from .error import GeoEngineException, InputException, UninitializedException, TypeException, \
    MethodNotCalledOnPlotException, MethodNotCalledOnRasterException, MethodNotCalledOnVectorException, \
    SpatialReferenceMismatchException, check_response_for_error, ModificationNotOnLayerDbException, \
    GeoEngineExceptionResponse, NoAdminSessionException
from .layers import Layer, LayerCollection, LayerListing, LayerCollectionListing, \
    LayerId, LayerCollectionId, LayerProviderId, \
    layer_collection, layer
from .types import QueryRectangle
from .workflow import WorkflowId, Workflow, workflow_by_id, register_workflow


DEFAULT_USER_AGENT = f'geoengine-python/{get_distribution("geoengine").version}'


def default_user_agent(_name="python-requests"):
    return DEFAULT_USER_AGENT


utils.default_user_agent = default_user_agent
