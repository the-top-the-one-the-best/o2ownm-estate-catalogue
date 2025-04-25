from marshmallow import fields, Schema

class XlsxUploadDto(Schema):
  xlsx = fields.Raw(required=True, type="file")

class EstateCustomerInfoImportOptionDto(Schema):
  auto_create_customer_tags = fields.Boolean(missing=False)
  overwrite_existing_user_by_phone = fields.Boolean(missing=False)
  timezone_offset = fields.Integer(missing=+8)
