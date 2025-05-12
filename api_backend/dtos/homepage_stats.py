from marshmallow import EXCLUDE, Schema, fields, validate
import pytz
from api_backend.dtos.estate_info import PublicEstateInfoDto
from api_backend.dtos.generic import GenericPagedQueryDto, create_page_result_dto
from api_backend.schemas import EstateInfoSchema, SystemLogSchema, ObjectIdHelper
from constants import AuthEventTypes, DataTargets, enum_set

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper
  
class EstateCustomerInfoTotalCountDto(Schema):
  estate_info_count = fields.Integer()
  customer_info_count = fields.Integer()
  class Meta:
    unknown = EXCLUDE

class RankedEstateInfoByCustomerInfoCount(PublicEstateInfoDto):
  customer_info_count = fields.Integer()
