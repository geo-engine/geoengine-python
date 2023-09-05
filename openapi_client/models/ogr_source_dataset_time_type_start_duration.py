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



from pydantic import BaseModel, Field, StrictStr, validator
from openapi_client.models.ogr_source_time_format import OgrSourceTimeFormat

class OgrSourceDatasetTimeTypeStartDuration(BaseModel):
    """
    OgrSourceDatasetTimeTypeStartDuration
    """
    duration_field: StrictStr = Field(..., alias="durationField")
    start_field: StrictStr = Field(..., alias="startField")
    start_format: OgrSourceTimeFormat = Field(..., alias="startFormat")
    type: StrictStr = Field(...)
    __properties = ["durationField", "startField", "startFormat", "type"]

    @validator('type')
    def type_validate_enum(cls, value):
        """Validates the enum"""
        if value not in ('startDuration'):
            raise ValueError("must be one of enum values ('startDuration')")
        return value

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
    def from_json(cls, json_str: str) -> OgrSourceDatasetTimeTypeStartDuration:
        """Create an instance of OgrSourceDatasetTimeTypeStartDuration from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.dict(by_alias=True,
                          exclude={
                          },
                          exclude_none=True)
        # override the default output from pydantic by calling `to_dict()` of start_format
        if self.start_format:
            _dict['startFormat'] = self.start_format.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> OgrSourceDatasetTimeTypeStartDuration:
        """Create an instance of OgrSourceDatasetTimeTypeStartDuration from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return OgrSourceDatasetTimeTypeStartDuration.parse_obj(obj)

        _obj = OgrSourceDatasetTimeTypeStartDuration.parse_obj({
            "duration_field": obj.get("durationField"),
            "start_field": obj.get("startField"),
            "start_format": OgrSourceTimeFormat.from_dict(obj.get("startFormat")) if obj.get("startFormat") is not None else None,
            "type": obj.get("type")
        })
        return _obj

