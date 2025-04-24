from marshmallow import EXCLUDE, Schema, fields
class QueryDistrictByNameSchema(Schema):
  l1_district = fields.String()
  class Meta:
    unknown = EXCLUDE
