from api_backend.schemas import (
  UserPermissionSchema,
  UserSchema,
  ObjectIdHelper,
)
from marshmallow import EXCLUDE, fields, Schema, validate

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper

# user
class CreateUserDto(Schema):
  email = fields.Email(allow_none=False, required=True)
  phone = fields.String(validate=validate.Regexp("^09\d{8}$"))
  name = fields.String(missing="")
  description = fields.String(missing="")
  permissions = fields.Nested(UserPermissionSchema)
  is_admin = fields.Boolean(missing=False)
  class Meta:
    unknown = EXCLUDE

class RequestResetPasswordDto(Schema):
  email = fields.Email(allow_none=False, required=True)
  class Meta:
    unknown = EXCLUDE

class UpdatePasswordDto(Schema):
  new_password = fields.String(required=True)
  old_password = fields.String()
  class Meta:
    unknown = EXCLUDE

class ResetPasswordDto(UpdatePasswordDto):
  salt = fields.String(required=True)
  class Meta:
    unknown = EXCLUDE

class UpdateUserDto(Schema):
  email = fields.Email()
  phone = fields.String(validate=validate.Regexp("^09\d{8}$"))
  name = fields.String()
  description = fields.String()
  class Meta:
    unknown = EXCLUDE

class UpdateUserPermissionDto(Schema):
  permissions = fields.Nested(UserPermissionSchema)
  is_admin = fields.Boolean(default=False)
  is_valid = fields.Boolean(default=False)
  class Meta:
    unknown = EXCLUDE

class PublicUserDto(UserSchema):
  class Meta:
    exclude = ('password',)

class CredentialDto(Schema):
  email = fields.Email(required=True)
  password = fields.String(required=True)
  class Meta:
    unknown = EXCLUDE

class LoginTokenDto(Schema):
  access_token = fields.String()
  refresh_token = fields.String()
  class Meta:
    unknown = EXCLUDE

class RefreshAccessTokenDto(Schema):
  refresh_token = fields.String(required=True)
  class Meta:
    unknown = EXCLUDE
