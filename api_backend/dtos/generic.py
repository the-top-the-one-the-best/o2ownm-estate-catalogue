from api_backend.schemas import (
  MongoDefaultDocumentSchema,
  ObjectIdHelper,
)
from marshmallow import EXCLUDE, fields, Schema

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
    matched_count = fields.Integer()
    class Meta:
      unknown = EXCLUDE

  return _PageResultDto

# general  
class GeneralInsertIdDto(MongoDefaultDocumentSchema):
  _id = fields.String()
