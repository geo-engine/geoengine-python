'''Tests ML functionality'''

import unittest
from sklearn.ensemble import RandomForestClassifier
from skl2onnx import to_onnx
import numpy as np
from geoengine_openapi_client.models import MlModelMetadata, RasterDataType
import geoengine as ge
from tests.ge_test import GeoEngineTestInstance


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

        # TODO: use `enterContext(cm)` instead of `with cm:` in Python 3.11
        with GeoEngineTestInstance() as ge_instance:
            ge_instance.wait_for_ready()

            ge.initialize(ge_instance.address())

            session = ge.get_session()
            model_name = f"{session.user_id}:foo"

            res_name = ge.register_ml_model(
                onnx_model=onnx_clf,
                model_config=ge.ml.MlModelConfig(
                    name=model_name,
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
            self.assertEqual(str(res_name), model_name)

            # Now test permission setting and removal
            ge.add_permission(
                ge.REGISTERED_USER_ROLE_ID, ge.Resource.from_ml_model_name(res_name), ge.Permission.READ
            )

            expected = ge.permissions.PermissionListing(
                permission=ge.Permission.READ,
                resource=ge.Resource.from_ml_model_name(res_name),
                role=ge.permissions.Role(ge.REGISTERED_USER_ROLE_ID, 'user')
            )

            self.assertIn(expected, ge.permissions.list_permissions(ge.Resource.from_ml_model_name(res_name)))

            ge.remove_permission(
                ge.REGISTERED_USER_ROLE_ID, ge.Resource.from_ml_model_name(res_name), ge.Permission.READ
            )

            self.assertNotIn(expected, ge.permissions.list_permissions(ge.Resource.from_ml_model_name(res_name)))

            # failing tests
            with self.assertRaises(ge.InputException) as exception:
                _res_name = ge.register_ml_model(
                    onnx_model=onnx_clf,
                    model_config=ge.ml.MlModelConfig(
                        name=model_name,
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
                _res_name = ge.register_ml_model(
                    onnx_model=onnx_clf,
                    model_config=ge.ml.MlModelConfig(
                        name=model_name,
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
                'Model input type `TensorProto.FLOAT` does not match the expected type `F64`'
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
                'Model output type `TensorProto.INT64` does not match the expected type `I32`'
            )
