'''
Util functions for machine learning
'''

from __future__ import annotations
from pathlib import Path
import tempfile
from dataclasses import dataclass
import geoengine_openapi_client.models
from onnx import TypeProto, TensorProto, ModelProto
from onnx.helper import tensor_dtype_to_string
from geoengine_openapi_client.models import MlModelMetadata, MlModel, RasterDataType, TensorShape3D
import geoengine_openapi_client
from geoengine.auth import get_session
from geoengine.datasets import UploadId
from geoengine.error import InputException


@dataclass
class MlModelConfig:
    '''Configuration for an ml model'''
    name: str
    metadata: MlModelMetadata
    display_name: str = "My Ml Model"
    description: str = "My Ml Model Description"


class MlModelName:
    '''A wrapper for an MlModel name'''

    __ml_model_name: str

    def __init__(self, ml_model_name: str) -> None:
        self.__ml_model_name = ml_model_name

    @classmethod
    def from_response(cls, response: geoengine_openapi_client.models.MlModelNameResponse) -> MlModelName:
        '''Parse a http response to an `DatasetName`'''
        return MlModelName(response.ml_model_name)

    def __str__(self) -> str:
        return self.__ml_model_name

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        '''Checks if two dataset names are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__ml_model_name == other.__ml_model_name  # pylint: disable=protected-access

    def to_api_dict(self) -> geoengine_openapi_client.models.MlModelNameResponse:
        return geoengine_openapi_client.models.MlModelNameResponse(
            ml_model_name=str(self.__ml_model_name)
        )


def register_ml_model(onnx_model: ModelProto,
                      model_config: MlModelConfig,
                      upload_timeout: int = 3600,
                      register_timeout: int = 60) -> MlModelName:
    '''Uploads an onnx file and registers it as an ml model'''

    validate_model_config(
        onnx_model,
        input_type=model_config.metadata.input_type,
        output_type=model_config.metadata.output_type,
        input_shape=model_config.metadata.input_shape,
        out_shape=model_config.metadata.output_shape
    )

    session = get_session()

    with geoengine_openapi_client.ApiClient(session.configuration) as api_client:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = Path(temp_dir) / model_config.metadata.file_name

            with open(file_name, 'wb') as file:
                file.write(onnx_model.SerializeToString())

            uploads_api = geoengine_openapi_client.UploadsApi(api_client)
            response = uploads_api.upload_handler([str(file_name)],
                                                  _request_timeout=upload_timeout)

        upload_id = UploadId.from_response(response)

        ml_api = geoengine_openapi_client.MLApi(api_client)

        model = MlModel(name=model_config.name, upload=str(upload_id), metadata=model_config.metadata,
                        display_name=model_config.display_name, description=model_config.description)
        res_name = ml_api.add_ml_model(model, _request_timeout=register_timeout)
        return MlModelName.from_response(res_name)


# pylint: disable=too-many-branches,too-many-statements
def validate_model_config(onnx_model: ModelProto, *,
                          input_type: RasterDataType,
                          output_type: RasterDataType,
                          input_shape: TensorShape3D,
                          out_shape: TensorShape3D):
    '''Validates the model config. Raises an exception if the model config is invalid'''

    def check_data_type(data_type: TypeProto, expected_type: RasterDataType, prefix: 'str'):
        if not data_type.tensor_type:
            raise InputException('Only tensor input types are supported')
        elem_type = data_type.tensor_type.elem_type
        if elem_type != RASTER_TYPE_TO_ONNX_TYPE[expected_type]:
            elem_type_str = tensor_dtype_to_string(elem_type)
            raise InputException(f'Model {prefix} type `{elem_type_str}` does not match the '
                                 f'expected type `{expected_type}`')

    model_inputs = onnx_model.graph.input
    model_outputs = onnx_model.graph.output

    if len(model_inputs) != 1:
        raise InputException('Models with multiple inputs are not supported')
    check_data_type(model_inputs[0].type, input_type, 'input')

    dim = model_inputs[0].type.tensor_type.shape.dim

    if len(dim) == 2:
        if not dim[1].dim_value:
            raise InputException('Dimension 1 of a 1D input tensor must have a length')
        if dim[1].dim_value != input_shape.attributes:
            raise InputException(f'Model input has {dim[1].dim_value} bands, but {input_shape.attributes} are expected')
    elif len(dim) == 4:
        if not dim[1].dim_value:
            raise InputException('Dimension 1 of the a 3D input tensor must have a length')
        if not dim[2].dim_value:
            raise InputException('Dimension 2 of the a 3D input tensor must have a length')
        if not dim[3].dim_value:
            raise InputException('Dimension 3 of the a 3D input tensor must have a length')
        if dim[1].dim_value != input_shape.y:
            raise InputException(f'Model input has {dim[1].dim_value} y size, but {input_shape.y} are expected')
        if dim[2].dim_value != input_shape.x:
            raise InputException(f'Model input has {dim[2].dim_value} x size, but {input_shape.x} are expected')
        if dim[3].dim_value != input_shape.attributes:
            raise InputException(f'Model input has {dim[3].dim_value} bands, but {input_shape.attributes} are expected')
    else:
        raise InputException('Only 1D and 3D input tensors are supported')

    if len(model_outputs) < 1:
        raise InputException('Models with no outputs are not supported')
    check_data_type(model_outputs[0].type, output_type, 'output')

    dim = model_outputs[0].type.tensor_type.shape.dim
    if len(dim) == 1:
        pass  # this is a happens if there is only a single out? so shape would be [-1]
    elif len(dim) == 2:
        if not dim[1].dim_value:
            raise InputException('Dimension 1 of a 1D input tensor must have a length')
        if dim[1].dim_value != 1:
            raise InputException(f'Model output has {dim[1].dim_value} bands, but {out_shape.attributes} are expected')
    elif len(dim) == 3:
        if not dim[1].dim_value:
            raise InputException('Dimension 1 of a 3D input tensor must have a length')
        if not dim[2].dim_value:
            raise InputException('Dimension 2 of a 3D input tensor must have a length')
        if dim[1].dim_value != out_shape.y:
            raise InputException(f'Model output has {dim[1].dim_value} y size, but {out_shape.y} are expected')
        if dim[2].dim_value != out_shape.x:
            raise InputException(f'Model output has {dim[2].dim_value} x size, but {out_shape.x} are expected')
    elif len(dim) == 4:
        if not dim[1].dim_value:
            raise InputException('Dimension 1 of the a 3D input tensor must have a length')
        if not dim[2].dim_value:
            raise InputException('Dimension 2 of the a 3D input tensor must have a length')
        if not dim[3].dim_value:
            raise InputException('Dimension 3 of the a 3D input tensor must have a length')
        if dim[1].dim_value != out_shape.y:
            raise InputException(f'Model output has {dim[1].dim_value} y size, but {out_shape.y} are expected')
        if dim[2].dim_value != out_shape.x:
            raise InputException(f'Model output has {dim[2].dim_value} x size, but {out_shape.x} are expected')
        if dim[3].dim_value != out_shape.attributes:
            raise InputException(f'Model output has {dim[3].dim_value} bands, but {out_shape.attributes} are expected')
    else:
        raise InputException('Only 1D and 3D output tensors are supported')


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
