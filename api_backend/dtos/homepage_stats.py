from marshmallow import EXCLUDE, Schema, fields
from api_backend.schemas import ObjectIdHelper

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper
  
class EstateCustomerInfoTotalCountDto(Schema):
  estate_info_count = fields.Integer()
  customer_info_count = fields.Integer()
  class Meta:
    unknown = EXCLUDE

class RankedEstateInfoByCustomerInfoCountDto(Schema):
  _id = fields.ObjectId()
  name = fields.String()
  customer_info_count = fields.Integer()

class RankedRegionInfoByEstateCountDto(Schema):
  class DistrictEstateCountDto(Schema):
    l1_district = fields.String(metadata={"example": "臺北市"})
    estate_info_count = fields.Integer(missing=0)
  region_name = fields.String(metadata={"example": "北部地區"})
  restion_stats = fields.List(fields.Nested(DistrictEstateCountDto))
