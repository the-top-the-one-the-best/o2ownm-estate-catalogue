from marshmallow import EXCLUDE, fields, Schema, validate
from api_backend.dtos.estate_info import PublicEstateInfoDto
from api_backend.dtos.generic import create_page_result_dto
from api_backend.schemas import CustomerInfoSchema, DistrictInfoSchema
from marshmallow.validate import Range
from constants import RoomLayouts, enum_set

class QueryCustomerInfoDto(Schema):
  estate_info_id = fields.ObjectId()
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  # Discrict query example:
  # 台北市全境 + 新北市三重區 = [
  #   { "l1_district": "新北市",  "l2_district": "三重區" },
  #   { "l1_district": "台北市" },
  # ]
  districts = fields.List(fields.Nested(DistrictInfoSchema))
  customer_tags = fields.List(fields.String())
  page_size = fields.Integer(missing=20, validate=[Range(min=1, max=100, error="Value must be in [1, 100]")])
  page_number = fields.Integer(missing=1, validate=[Range(min=1, error="Value must >= 1")])
  class Meta:
    unknown = EXCLUDE

class PublicCustomerInfoDto(CustomerInfoSchema):
  estate_info = fields.Nested(PublicEstateInfoDto)

PagedCustomerInfoDto = create_page_result_dto(CustomerInfoSchema)
