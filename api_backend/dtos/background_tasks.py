from marshmallow import fields, Schema
from marshmallow.validate import Range

class XlsxUploadDto(Schema):
  xlsx = fields.Raw(required=True, type="file")
