'''
Util functions for machine learning
'''

from pathlib import Path
import tempfile
from typing import Protocol
from dataclasses import dataclass
from geoengine_openapi_client.models import MlModelMetadata, MlModel
import geoengine_openapi_client
from geoengine.auth import get_session
from geoengine.datasets import UploadId


# pylint: disable=invalid-name
class SerializableModel(Protocol):
    '''A protocol for serializable models'''

    def SerializeToString(self) -> bytes:
        ...


@dataclass
class MlModelConfig:
    '''Configuration for an ml model'''
    name: str
    metadata: MlModelMetadata
    file_name: str = "model.onnx"
    display_name: str = "My Ml Model"
    description: str = "My Ml Model Description"


def register_ml_model(onnx_model: SerializableModel,
                      model_config: MlModelConfig,
                      upload_timeout: int = 3600,
                      register_timeout: int = 60):
    '''Uploads an onnx file and registers it as an ml model'''

    session = get_session()

    with geoengine_openapi_client.ApiClient(session.configuration) as api_client:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = Path(temp_dir) / model_config.file_name

            with open(file_name, 'wb') as file:
                file.write(onnx_model.SerializeToString())

            uploads_api = geoengine_openapi_client.UploadsApi(api_client)
            response = uploads_api.upload_handler([str(file_name)],
                                                  _request_timeout=upload_timeout)

        upload_id = UploadId.from_response(response)

        ml_api = geoengine_openapi_client.MLApi(api_client)

        model = MlModel(name=model_config.name, upload=str(upload_id), metadata=model_config.metadata,
                        display_name=model_config.display_name, description=model_config.description)
        ml_api.add_ml_model(model, _request_timeout=register_timeout)
