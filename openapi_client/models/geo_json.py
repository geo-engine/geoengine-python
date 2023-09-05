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


from typing import List
from pydantic import BaseModel, Field, conlist
from openapi_client.models.collection_type import CollectionType
from openapi_client.models.feature import Feature

class GeoJson(BaseModel):
    """
    GeoJson
    """
    features: conlist(Feature) = Field(...)
    type: CollectionType = Field(...)
    __properties = ["features", "type"]

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
    def from_json(cls, json_str: str) -> GeoJson:
        """Create an instance of GeoJson from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.dict(by_alias=True,
                          exclude={
                          },
                          exclude_none=True)
        # override the default output from pydantic by calling `to_dict()` of each item in features (list)
        _items = []
        if self.features:
            for _item in self.features:
                if _item:
                    _items.append(_item.to_dict())
            _dict['features'] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> GeoJson:
        """Create an instance of GeoJson from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return GeoJson.parse_obj(obj)

        _obj = GeoJson.parse_obj({
            "features": [Feature.from_dict(_item) for _item in obj.get("features")] if obj.get("features") is not None else None,
            "type": obj.get("type")
        })
        return _obj

