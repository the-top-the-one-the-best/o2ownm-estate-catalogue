from api_backend.schemas import (
  UserPermissionSchema,
  UserSchema,
  ObjectIdHelper,
)
from marshmallow import fields, Schema, validate

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

class RequestResetPasswordDto(Schema):
  email = fields.Email(allow_none=False, required=True)

class UpdatePasswordDto(Schema):
  new_password = fields.String(required=True)

class ResetPasswordDto(UpdatePasswordDto):
  salt = fields.String(required=True)

class UpdateUserDto(Schema):
  email = fields.Email(allow_none=False, required=True)
  phone = fields.String(validate=validate.Regexp("^09\d{8}$"))
  name = fields.String()
  description = fields.String()

class UpdateUserPermissionDto(Schema):
  permissions = fields.Nested(UserPermissionSchema)
  is_admin = fields.Boolean(default=False)
  is_valid = fields.Boolean(default=False)

class PublicUserDto(UserSchema):
  class Meta:
    exclude = ('password',)

class CredentialDto(Schema):
  email = fields.Email(required=True)
  password = fields.String(required=True)

class LoginTokenDto(Schema):
  access_token = fields.String()
  refresh_token = fields.String()

class RefreshAccessTokenDto(Schema):
  refresh_token = fields.String(required=True)
