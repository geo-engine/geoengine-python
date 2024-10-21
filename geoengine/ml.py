'''
Util functions for machine learning
'''

from pathlib import Path
import tempfile
from typing import Protocol
from dataclasses import dataclass
from onnx.reference import ReferenceEvaluator
from onnx import TypeProto, TensorProto, ModelProto
from onnx.helper import tensor_dtype_to_string
from geoengine_openapi_client.models import MlModelMetadata, MlModel, RasterDataType
import geoengine_openapi_client
from geoengine.auth import get_session
from geoengine.datasets import UploadId
from geoengine.error import InputException


@dataclass
class MlModelConfig:
    '''Configuration for an ml model'''
    name: str
    metadata: MlModelMetadata
    file_name: str = "model.onnx"
    display_name: str = "My Ml Model"
    description: str = "My Ml Model Description"


def register_ml_model(onnx_model: ModelProto,
                      model_config: MlModelConfig,
                      upload_timeout: int = 3600,
                      register_timeout: int = 60):
    '''Uploads an onnx file and registers it as an ml model'''

    validate_model_config(
        onnx_model,
        input_type=model_config.metadata.input_type,
        output_type=model_config.metadata.output_type,
        num_input_bands=model_config.metadata.num_input_bands,
    )

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


def validate_model_config(onnx_model: ModelProto, *,
                          input_type: RasterDataType,
                          output_type: RasterDataType,
                          num_input_bands: int):
    '''Validates the model config. Raises an exception if the model config is invalid'''

    def check_data_type(data_type: TypeProto, expected_type: RasterDataType, prefix: 'str'):
        if not data_type.tensor_type:
            raise InputException('Only tensor input types are supported')
        elem_type = data_type.tensor_type.elem_type
        if elem_type != RASTER_TYPE_TO_ONNX_TYPE[expected_type]:
            elem_type_str = tensor_dtype_to_string(elem_type)
            raise InputException(f'Model {prefix} type `{elem_type_str}` does not match the '
                                 f'expected type `{expected_type}`')

    for domain in onnx_model.opset_import:
        if domain.domain != '':
            continue
        if domain.version != 9:
            raise InputException('Only ONNX models with opset version 9 are supported')

    try:
        model_ref = ReferenceEvaluator(onnx_model)
    except NotImplementedError as e:
        if 'ZipMap' in str(e):
            raise InputException(
                'ZipMap is not supported in the model. Consider setting `options={"zipmap": False}`'
            ) from e
        raise e  # just re-raise

    if len(model_ref.input_types) != 1:
        raise InputException('Models with multiple inputs are not supported')
    check_data_type(model_ref.input_types[0], input_type, 'input')

    dims = model_ref.input_types[0].tensor_type.shape.dim
    if len(dims) != 2:
        raise InputException('Only 2D input tensors are supported')
    if not dims[1].dim_value:
        raise InputException('Dimension 1 of the input tensor must have a length')
    if dims[1].dim_value != num_input_bands:
        raise InputException(f'Model input has {dims[1].dim_value} bands, but {num_input_bands} bands are expected')

    if len(model_ref.output_types) < 1:
        raise InputException('Models with no outputs are not supported')
    check_data_type(model_ref.output_types[0], output_type, 'output')


RASTER_TYPE_TO_ONNX_TYPE = {
    RasterDataType.F32: TensorProto.FLOAT,
    RasterDataType.F64: TensorProto.DOUBLE,
    RasterDataType.U8: TensorProto.UINT8,
    RasterDataType.U16: TensorProto.UINT16,
    RasterDataType.U32: TensorProto.UINT32,
    RasterDataType.U64: TensorProto.UINT64,
    RasterDataType.I8: TensorProto.INT8,
    RasterDataType.I16: TensorProto.INT16,
    RasterDataType.I32: TensorProto.INT32,
    RasterDataType.I64: TensorProto.INT64,
}
