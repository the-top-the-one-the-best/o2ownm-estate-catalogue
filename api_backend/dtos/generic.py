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
class GenericRankQueryDto(Schema):
  limit = fields.Integer(
    missing=10,
    validate=[Range(min=1, max=200)],
    metadata={ "example":  10 },
  )

class GenericInsertIdDto(MongoDefaultDocumentSchema):
  _id = fields.String()

from typing import TypeVar, Type
T = TypeVar("T", bound=Schema)
def create_page_result_dto(item_schema: Type[Schema]):
  class PageResultDto(Schema):
    results = fields.List(fields.Nested(item_schema))
    page_size = fields.Integer()
    page_number = fields.Integer()
    has_more = fields.Boolean()

    # matched count is for preview of export tasks
    matched_count = fields.Integer()
    class Meta:
      unknown = EXCLUDE

  PageResultDto.__name__ = PageResultDto.__name__ + "<" + item_schema.__name__ + ">"
  return PageResultDto

class GenericPagedQueryDto(Schema):
  count_matched = fields.Boolean(missing=False, default=False)
  page_size = fields.Integer(
    missing=20,
    validate=[Range(min=1, max=200)],
    metadata={ "example":  20 },
  )
  page_number = fields.Integer(
    missing=1,
    validate=[Range(min=1, error="Value must >= 1")],
    metadata={ "example":  1 },
  )

class GenericMatchCountDto(Schema):
  grouped_fields = fields.List(fields.String(metadata={ "example": "phone" }))
  matched_count = fields.Integer(missing=0)
  distinct_matched_count = fields.Integer(missing=0)
