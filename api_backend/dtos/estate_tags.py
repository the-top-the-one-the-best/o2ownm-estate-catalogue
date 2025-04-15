from marshmallow import EXCLUDE, fields, Schema, post_load
from api_backend.dtos.generic import GeneralPagedQueryDto, create_page_result_dto
from api_backend.schemas import EstateTagSchema

class QueryEstageTagDto(GeneralPagedQueryDto):
  name = fields.String()
  is_frequently_used = fields.Boolean()
  class Meta:
    unknown = EXCLUDE
    
class UpsertEstateTagDto(Schema):
  name = fields.String()
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

PagedEstateTagDto = create_page_result_dto(EstateTagSchema)
