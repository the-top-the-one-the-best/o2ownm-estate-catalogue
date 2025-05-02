from marshmallow import EXCLUDE, fields, Schema, post_load
from marshmallow.validate import Length
from api_backend.dtos.generic import GenericPagedQueryDto, create_page_result_dto
from api_backend.schemas import CustomerTagSchema
class QueryCustomerTagDto(GenericPagedQueryDto):
  name = fields.String()
  is_frequently_used = fields.Boolean()
  class Meta:
    unknown = EXCLUDE
    
class UpsertCustomerTagDto(Schema):
  name = fields.String(validate=Length(min=1, max=12))
  description = fields.String(missing="")
  is_frequently_used = fields.Boolean(missing=False)
  class Meta:
    unknown = EXCLUDE
    
  @post_load
  def post_load_handler(self, data, **kwargs):
    if type(data.get("name")) is str:
      data["name"] = data["name"].strip()
    if type(data.get("description")) is str:
      data["description"] = data["description"].strip()
    return data

PagedCustomerTagDto = create_page_result_dto(CustomerTagSchema)
