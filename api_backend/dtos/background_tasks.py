from marshmallow import fields, Schema

class XlsxUploadDto(Schema):
  xlsx = fields.Raw(required=True, type="file")
