from api_backend.dtos.generic import create_page_result_dto
from api_backend.dtos.user import PublicUserDto
from api_backend.schemas import (
  _DescriptionSchema,
  LatestNewsSchema,
  ObjectIdHelper,
)
from marshmallow import fields, Schema
from marshmallow.validate import Range

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper

# latest news
class PublicLatestNewsDto(LatestNewsSchema):
  creator = fields.Nested(PublicUserDto)
  updater = fields.Nested(PublicUserDto)

class UpsertLatestNewsDto(Schema):
  title = fields.String()
  description = fields.List(fields.Nested(_DescriptionSchema))
  start_time = fields.AwareDateTime()
  end_time = fields.AwareDateTime()

class QueryLatestNewsDto(Schema):
  _ids = fields.List(fields.ObjectId)
  creator_id = fields.ObjectId()
  updater_id = fields.ObjectId()
  with_user_info = fields.Integer(missing=0)
  page_size = fields.Integer(missing=20, validate=[Range(min=1, max=100, error="Value must be in [1, 100]")])
  page_number = fields.Integer(missing=1, validate=[Range(min=1, error="Value must >= 1")])

PagedLatestNewsDto = create_page_result_dto(PublicLatestNewsDto)
