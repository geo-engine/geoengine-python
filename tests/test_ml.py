'''Tests ML functionality'''

import unittest
from sklearn.ensemble import RandomForestClassifier
from skl2onnx import to_onnx
import numpy as np
from geoengine_openapi_client.models import MlModelMetadata, RasterDataType
import geoengine as ge
from . import UrllibMocker


class WorkflowStorageTests(unittest.TestCase):
    '''Test methods for storing workflows as datasets'''

    def setUp(self) -> None:
        ge.reset(False)

    def test_uploading_onnx_model(self):

        clf = RandomForestClassifier(random_state=42)
        training_x = np.array([[1, 2], [3, 4]], dtype=np.float32)
        training_y = np.array([0, 1], dtype=np.int64)
        clf.fit(training_x, training_y)

        onnx_clf = to_onnx(clf, training_x[:1], options={'zipmap': False}, target_opset=9)
        onnx_clf2 = to_onnx(clf, training_x[:1], options={'zipmap': False}, target_opset=12)

        with UrllibMocker() as m:
            session_id = "c4983c3e-9b53-47ae-bda9-382223bd5081"
            request_headers = {'Authorization': f'Bearer {session_id}'}

            m.post('http://mock-instance/anonymous', json={
                "id": session_id,
                "project": None,
                "view": None
            })

            upload_id = "c314ff6d-3e37-41b4-b9b2-3669f13f7369"

            m.post('http://mock-instance/upload', json={
                "id": upload_id
            }, request_headers=request_headers)

            m.post('http://mock-instance/ml/models',
                   expected_request_body={
                       "description": "A simple decision tree model",
                       "displayName": "Decision Tree",
                       "metadata": {
                           "fileName": "model.onnx",
                           "inputType": "F32",
                           "numInputBands": 2,
                           "outputType": "I64"
                       },
                       "name": "foo",
                       "upload": upload_id
                   },
                   request_headers=request_headers)

            ge.initialize("http://mock-instance")

            ge.register_ml_model(
                onnx_model=onnx_clf,
                model_config=ge.ml.MlModelConfig(
                    name="foo",
                    metadata=MlModelMetadata(
                        file_name="model.onnx",
                        input_type=RasterDataType.F32,
                        num_input_bands=2,
                        output_type=RasterDataType.I64,
                    ),
                    display_name="Decision Tree",
                    description="A simple decision tree model",
                )
            )

            with self.assertRaises(ge.InputException) as exception:
                ge.register_ml_model(
                    onnx_model=onnx_clf,
                    model_config=ge.ml.MlModelConfig(
                        name="foo",
                        metadata=MlModelMetadata(
                            file_name="model.onnx",
                            input_type=RasterDataType.F32,
                            num_input_bands=4,
                            output_type=RasterDataType.I64,
                        ),
                        display_name="Decision Tree",
                        description="A simple decision tree model",
                    )
                )
            self.assertEqual(
                str(exception.exception),
                'Model input has 2 bands, but 4 bands are expected'
            )

            with self.assertRaises(ge.InputException) as exception:
                ge.register_ml_model(
                    onnx_model=onnx_clf,
                    model_config=ge.ml.MlModelConfig(
                        name="foo",
                        metadata=MlModelMetadata(
                            file_name="model.onnx",
                            input_type=RasterDataType.F64,
                            num_input_bands=2,
                            output_type=RasterDataType.I64,
                        ),
                        display_name="Decision Tree",
                        description="A simple decision tree model",
                    )
                )
            self.assertEqual(
                str(exception.exception),
                'Model input type `TensorProto.FLOAT` does not match the expected type `RasterDataType.F64`'
            )

            with self.assertRaises(ge.InputException) as exception:
                ge.register_ml_model(
                    onnx_model=onnx_clf,
                    model_config=ge.ml.MlModelConfig(
                        name="foo",
                        metadata=MlModelMetadata(
                            file_name="model.onnx",
                            input_type=RasterDataType.F32,
                            num_input_bands=2,
                            output_type=RasterDataType.I32,
                        ),
                        display_name="Decision Tree",
                        description="A simple decision tree model",
                    )
                )
            self.assertEqual(
                str(exception.exception),
                'Model output type `TensorProto.INT64` does not match the expected type `RasterDataType.I32`'
            )
