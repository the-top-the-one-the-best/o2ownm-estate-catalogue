from marshmallow import fields, Schema

class XlsxUploadDto(Schema):
  xlsx = fields.Raw(required=True, type="file")

class EstateCustomerInfoImportOptionDto(Schema):
  timezone_offset = fields.Integer(missing=+8)
