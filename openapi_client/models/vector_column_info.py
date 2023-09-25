# coding: utf-8

"""
    Geo Engine Pro API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 0.7.0
    Contact: dev@geoengine.de
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json



from pydantic import BaseModel, Field
from openapi_client.models.feature_data_type import FeatureDataType
from openapi_client.models.measurement import Measurement

class VectorColumnInfo(BaseModel):
    """
    VectorColumnInfo
    """
    data_type: FeatureDataType = Field(..., alias="dataType")
    measurement: Measurement = Field(...)
    __properties = ["dataType", "measurement"]

    class Config:
        """Pydantic configuration"""
        allow_population_by_field_name = True
        validate_assignment = True

    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.dict(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> VectorColumnInfo:
        """Create an instance of VectorColumnInfo from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.dict(by_alias=True,
                          exclude={
                          },
                          exclude_none=True)
        # override the default output from pydantic by calling `to_dict()` of measurement
        if self.measurement:
            _dict['measurement'] = self.measurement.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> VectorColumnInfo:
        """Create an instance of VectorColumnInfo from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return VectorColumnInfo.parse_obj(obj)

        _obj = VectorColumnInfo.parse_obj({
            "data_type": obj.get("dataType"),
            "measurement": Measurement.from_dict(obj.get("measurement")) if obj.get("measurement") is not None else None
        })
        return _obj

