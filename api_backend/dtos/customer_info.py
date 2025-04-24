from marshmallow import EXCLUDE, fields, Schema, post_dump, post_load, validate
import pytz
from api_backend.dtos.estate_info import PublicEstateInfoDto
from api_backend.dtos.generic import GeneralPagedQueryDto, create_page_result_dto
from api_backend.schemas import CustomerInfoSchema, DistrictInfoSchema, RoomSizeSchema
from marshmallow.validate import Range
from constants import RoomLayouts, enum_set

class QueryCustomerInfoDto(GeneralPagedQueryDto):
  estate_info_id = fields.ObjectId()
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  # Discrict query example:
  # 臺北市全境 + 新北市三重區 = [
  #   { "l1_district": "新北市",  "l2_district": "三重區" },
  #   { "l1_district": "臺北市" },
  # ]
  districts = fields.List(fields.Nested(DistrictInfoSchema))
  room_size = fields.Nested(RoomSizeSchema())
  customer_tags = fields.List(fields.ObjectId())
  class Meta:
    unknown = EXCLUDE

class PublicCustomerInfoDto(CustomerInfoSchema):
  estate_info = fields.Nested(PublicEstateInfoDto)

class UpsertCustomerInfoDto(Schema):
  estate_info_id = fields.ObjectId()
  name = fields.String(missing="")
  title_pronoun = fields.String(missing="")
  phone = fields.String(missing="", metadata={"example": "0987654321"})
  email = fields.String(validate=lambda x: x == "" or validate.Email(), metadata={"example": "user@example.com"})
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  room_sizes = fields.List(fields.Nested(RoomSizeSchema()))
  info_date = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  l1_district = fields.String(allow_none=True, missing=None, metadata={ "example": "臺南市" })
  l2_district = fields.String(allow_none=True, missing=None, metadata={ "example": "東區" })
  customer_tags = fields.List(fields.ObjectId())
  class Meta:
    unknown = EXCLUDE
  def __arrange_data__(self, data):
    if type(data.get("name")) is str:
      data["name"] = data["name"].strip()
    if type(data.get("title_pronoun")) is str:
      data["title_pronoun"] = data["title_pronoun"].strip()
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    if type(data.get("phone")) is str:
      data["phone"] = data["phone"].strip()
    if type(data.get("room_layouts")) is list:
      data["room_layouts"] = sorted(data["room_layouts"])
    if type(data.get("customer_tags")) is list:
      data["customer_tags"] = sorted(data["customer_tags"])
    return data
  @post_load
  def post_load_handler(self, data, **kwargs):
    return self.__arrange_data__(data)
  @post_dump
  def post_dump_handler(self, data, **kwargs):
    return self.__arrange_data__(data)
  
PagedCustomerInfoDto = create_page_result_dto(CustomerInfoSchema)
