from marshmallow import fields, Schema
from marshmallow.validate import Range

class ImageUploadResultDto(Schema):
  url = fields.Url()
  new_width = fields.Integer()
  new_height = fields.Integer()

class ImageUploadDto(Schema):
  image = fields.Raw(required=True, type="file")
  
class ImageUploadQueryDto(Schema):
  preferred_max_size = fields.Int(missing=2048, validate=[Range(min=1, max=4096, error="Value must be in [1, 4096]")])

class MemberXlsxUploadDto(Schema):
  xlsx = fields.Raw(required=True, type="file")