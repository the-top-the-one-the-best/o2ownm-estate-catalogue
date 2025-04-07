from marshmallow import EXCLUDE, fields, Schema
from api_backend.dtos.generic import create_page_result_dto
from api_backend.schemas import CustomerInfoSchema
from marshmallow.validate import Range

class QueryCustomerInfoDto(Schema):
  # match fields
  name_zh = fields.String(missing=None, allow_none=True)
  civ_id = fields.String(missing=None, allow_none=True)
  gender = fields.Integer(allow_none=True)
  student_id = fields.String(missing=None, allow_none=True)
  graduate_year = fields.Integer(missing=None, allow_none=True)
  
  # text search fields
  # graduate_dept, graduate_dept_code, address_contact,
  # address_registered, phone_contact, phone_registered,
  fulltext_query = fields.String(missing=None, allow_none=True)
  page_size = fields.Integer(missing=20, validate=[Range(min=1, max=100, error="Value must be in [1, 100]")])
  page_number = fields.Integer(missing=1, validate=[Range(min=1, error="Value must >= 1")])
  class Meta:
    unknown = EXCLUDE
    
PagedCustomerInfoDto = create_page_result_dto(CustomerInfoSchema)
