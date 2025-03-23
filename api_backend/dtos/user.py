from api_backend.schemas import (
  UserSchema,
  ObjectIdHelper,
)
from marshmallow import fields, Schema

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper

# user
class CreateUserDto(UserSchema):
  class Meta:
    exclude = (
      '_id',
      'created_at',
      'updated_at',
    )

class UpdatePasswordDto(Schema):
  new_password = fields.String()

class UpdateUserDto(UserSchema):
  class Meta:
    exclude = (
      '_id',
      'password',
      'created_at',
      'updated_at',
      'is_admin',
      'is_active',
    )

class PublicUserDto(UserSchema):
  class Meta:
    exclude = ('password', )

class CredentialDto(Schema):
  email = fields.Email(required=True)
  password = fields.String(required=True)

class LoginTokenDto(Schema):
  access_token = fields.String()
  refresh_token = fields.String()
