from marshmallow import EXCLUDE, fields, Schema, validate
from api_backend.dtos.generic import create_page_result_dto
from api_backend.schemas import DistrictInfoSchema, EstateInfoSchema, RoomSizeSchema
from marshmallow.validate import Range
from constants import RoomLayouts, enum_set

class UpsertEstateInfoDto(Schema):
  name = fields.String(required=True)
  construction_company = fields.String(missing="")
  address = fields.String(missing="")
  l1_district = fields.String(allow_none=True, missing=None, metadata={"example": "台南市"})
  l2_district = fields.String(allow_none=True, missing=None, metadata={"example": "東區"})
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  room_sizes = fields.List(fields.Nested(RoomSizeSchema()))
  estate_tags = fields.List(fields.String())

class QueryEstateInfoDto(Schema):
  name = fields.String()
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  # Discrict query example:
  # 台北市全境 + 新北市三重區 = [
  #   { "l1_district": "新北市",  "l2_district": "三重區" },
  #   { "l1_district": "台北市" },
  # ]
  districts = fields.List(fields.Nested(DistrictInfoSchema))
  estate_tags = fields.List(fields.String())
  page_size = fields.Integer(missing=20, validate=[Range(min=1, max=100, error="Value must be in [1, 100]")])
  page_number = fields.Integer(missing=1, validate=[Range(min=1, error="Value must >= 1")])
  class Meta:
    unknown = EXCLUDE

class PublicEstateInfoDto(EstateInfoSchema):
  pass

PagedEstateInfoDto = create_page_result_dto(PublicEstateInfoDto)
