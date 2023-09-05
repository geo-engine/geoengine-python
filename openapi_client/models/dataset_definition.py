# coding: utf-8

"""
    Geo Engine API

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
from openapi_client.models.add_dataset import AddDataset
from openapi_client.models.meta_data_definition import MetaDataDefinition

class DatasetDefinition(BaseModel):
    """
    DatasetDefinition
    """
    meta_data: MetaDataDefinition = Field(..., alias="metaData")
    properties: AddDataset = Field(...)
    __properties = ["metaData", "properties"]

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
    def from_json(cls, json_str: str) -> DatasetDefinition:
        """Create an instance of DatasetDefinition from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.dict(by_alias=True,
                          exclude={
                          },
                          exclude_none=True)
        # override the default output from pydantic by calling `to_dict()` of meta_data
        if self.meta_data:
            _dict['metaData'] = self.meta_data.to_dict()
        # override the default output from pydantic by calling `to_dict()` of properties
        if self.properties:
            _dict['properties'] = self.properties.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> DatasetDefinition:
        """Create an instance of DatasetDefinition from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return DatasetDefinition.parse_obj(obj)

        _obj = DatasetDefinition.parse_obj({
            "meta_data": MetaDataDefinition.from_dict(obj.get("metaData")) if obj.get("metaData") is not None else None,
            "properties": AddDataset.from_dict(obj.get("properties")) if obj.get("properties") is not None else None
        })
        return _obj

