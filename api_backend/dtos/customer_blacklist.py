from marshmallow import EXCLUDE, fields, Schema, post_dump, post_load
from api_backend.dtos.generic import GenericPagedQueryDto, create_page_result_dto
from api_backend.schemas import CustomerBlacklistSchema

class FilterCustomerBlacklistDto(Schema):
  name = fields.String(metadata={ "example": "王亂打" })
  phone = fields.String(metadata={"example": "886987654321"})
  class Meta:
    unknown = EXCLUDE

class QueryCustomerBlacklistDto(FilterCustomerBlacklistDto, GenericPagedQueryDto):
  class Meta:
    unknown = EXCLUDE

class UpsertCustomerBlacklistDto(Schema):
  name = fields.String(missing="",metadata={ "example": "王亂打" })
  phone = fields.String(missing="", metadata={"example": "886987654321"})
  class Meta:
    unknown = EXCLUDE
  def __arrange_data__(self, data):
    if type(data.get("name")) is str:
      data["name"] = data["name"].strip()
    if type(data.get("phone")) is str:
      data["phone"] = data["phone"].strip()
    return data
  @post_load
  def post_load_handler(self, data, **kwargs):
    return self.__arrange_data__(data)
  @post_dump
  def post_dump_handler(self, data, **kwargs):
    return self.__arrange_data__(data)
  
PagedCustomerBlacklistDto = create_page_result_dto(CustomerBlacklistSchema)
