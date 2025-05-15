from marshmallow import EXCLUDE, fields, Schema, post_dump, post_load, validate
from api_backend.dtos.generic import GenericPagedQueryDto, create_page_result_dto
from api_backend.schemas import (
  DistrictInfoSchema,
  EstateInfoSchema,
  ObjectIdHelper,
  RoomSizeSchema,
)
from constants import RoomLayouts, enum_set

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper
  
class UpsertEstateInfoDto(Schema):
  name = fields.String(required=True)
  construction_company = fields.String(missing="")
  address = fields.String(missing="")
  l1_district = fields.String(allow_none=True, missing=None, metadata={ "example": "臺南市" })
  l2_district = fields.String(allow_none=True, missing=None, metadata={ "example": "東區" })
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  room_sizes = fields.List(fields.Nested(RoomSizeSchema()))
  estate_tags = fields.List(fields.ObjectId())
  class Meta:
    unknown = EXCLUDE
  def __arrange_data__(self, data):
    if type(data.get("name")) is str:
      data["name"] = data["name"].strip()
    if type(data.get("construction_company")) is str:
      data["construction_company"] = data["construction_company"].strip()
    if type(data.get("address")) is str:
      data["room_layouts"] = sorted(data["room_layouts"])
    if type(data.get("estate_tags")) is list:
      data["estate_tags"] = sorted(data["estate_tags"])
    return data
  @post_load
  def post_load_handler(self, data, **kwargs):
    return self.__arrange_data__(data)
  @post_dump
  def post_dump_handler(self, data, **kwargs):
    return self.__arrange_data__(data)
  
class QueryEstateInfoDto(GenericPagedQueryDto):
  _ids = fields.List(fields.ObjectId)
  name = fields.String()
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  # Discrict query example:
  # 臺北市全境 + 新北市三重區 = [
  #   { "l1_district": "新北市",  "l2_district": "三重區" },
  #   { "l1_district": "臺北市" },
  # ]
  districts = fields.List(fields.Nested(DistrictInfoSchema))
  room_size = fields.Nested(RoomSizeSchema())
  estate_tags = fields.List(fields.ObjectId())
  class Meta:
    unknown = EXCLUDE

class PublicEstateInfoDto(EstateInfoSchema):
  class Meta:
    unknown = EXCLUDE

PagedEstateInfoDto = create_page_result_dto(PublicEstateInfoDto)
