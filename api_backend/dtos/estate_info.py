from marshmallow import EXCLUDE, fields, Schema, validate
from api_backend.dtos.generic import GeneralPagedQueryDto, create_page_result_dto
from api_backend.schemas import DistrictInfoSchema, EstateInfoSchema, ObjectIdHelper, RoomSizeSchema
from marshmallow.validate import Range
from constants import RoomLayouts, enum_set

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper
  
class UpsertEstateInfoDto(Schema):
  name = fields.String(required=True)
  construction_company = fields.String(missing="")
  address = fields.String(missing="")
  l1_district = fields.String(allow_none=True, missing=None, metadata={ "example": "台南市" })
  l2_district = fields.String(allow_none=True, missing=None, metadata={ "example": "東區" })
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  room_sizes = fields.List(fields.Nested(RoomSizeSchema()))
  estate_tags = fields.List(fields.String())

class QueryEstateInfoDto(GeneralPagedQueryDto):
  _ids = fields.List(fields.ObjectId)
  name = fields.String()
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  # Discrict query example:
  # 台北市全境 + 新北市三重區 = [
  #   { "l1_district": "新北市",  "l2_district": "三重區" },
  #   { "l1_district": "台北市" },
  # ]
  districts = fields.List(fields.Nested(DistrictInfoSchema))
  room_size = fields.Nested(RoomSizeSchema())
  estate_tags = fields.List(fields.String())
  class Meta:
    unknown = EXCLUDE

class PublicEstateInfoDto(EstateInfoSchema):
  class Meta:
    unknown = EXCLUDE

PagedEstateInfoDto = create_page_result_dto(PublicEstateInfoDto)
