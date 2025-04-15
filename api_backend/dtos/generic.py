from api_backend.schemas import (
  MongoDefaultDocumentSchema,
  ObjectIdHelper,
)
from marshmallow import EXCLUDE, fields, Schema
from marshmallow.validate import Range

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper

# general  
class GeneralInsertIdDto(MongoDefaultDocumentSchema):
  _id = fields.String()

from typing import TypeVar, Type
T = TypeVar("T", bound=Schema)
def create_page_result_dto(item_schema: Type[Schema]):
  class _PageResultDto(Schema):
    results = fields.List(fields.Nested(item_schema))
    page_size = fields.Integer()
    page_number = fields.Integer()
    has_more = fields.Boolean()

    # matched count is for preview of export tasks
    matched_count = fields.Integer()
    class Meta:
      unknown = EXCLUDE

  return _PageResultDto

class GeneralPagedQueryDto(Schema):
  page_size = fields.Integer(
    missing=20,
    validate=[Range(min=1, max=100, error="Value must be in [1, 100]")],
    metadata={ "example":  20 },
  )
  page_number = fields.Integer(
    missing=1,
    validate=[Range(min=1, error="Value must >= 1")],
    metadata={ "example":  1 },
  )
