from api_backend.dtos.generic import GeneralPagedQueryDto, create_page_result_dto
from api_backend.schemas import (
  UserPermissionSchema,
  UserSchema,
  ObjectIdHelper,
)
from marshmallow import EXCLUDE, fields, Schema, post_dump, post_load, validate

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
  @post_load
  def post_load_handler(self, data, **kwargs):
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    return data
  @post_dump
  def post_dump_handler(self, data, **kwargs):
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    return data

class RequestResetPasswordDto(Schema):
  email = fields.Email(allow_none=False, required=True)
  class Meta:
    unknown = EXCLUDE
  @post_load
  def post_load_handler(self, data, **kwargs):
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    return data
  @post_dump
  def post_dump_handler(self, data, **kwargs):
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    return data

class UserQueryDto(GeneralPagedQueryDto):
  name = fields.String()
  email = fields.String()

class UpdatePasswordDto(Schema):
  old_password = fields.String()
  new_password = fields.String(required=True)
  class Meta:
    unknown = EXCLUDE

class ResetPasswordDto(Schema):
  salt = fields.String(required=True)
  new_password = fields.String(required=True)
  class Meta:
    unknown = EXCLUDE

class UpdateUserDto(Schema):
  email = fields.Email()
  phone = fields.String(validate=validate.Regexp("^09\d{8}$"))
  name = fields.String()
  description = fields.String()
  class Meta:
    unknown = EXCLUDE
  @post_load
  def post_load_handler(self, data, **kwargs):
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    return data
  @post_dump
  def post_dump_handler(self, data, **kwargs):
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    return data

class UpdateUserPermissionDto(Schema):
  permissions = fields.Nested(UserPermissionSchema)
  is_admin = fields.Boolean(default=False)
  is_valid = fields.Boolean(default=False)
  class Meta:
    unknown = EXCLUDE

class PublicUserDto(UserSchema):
  class Meta:
    exclude = ('password',)

PagedPublicUserDto = create_page_result_dto(PublicUserDto)

class CredentialDto(Schema):
  email = fields.Email(required=True, metadata={"example": "alexchiu@bclab.ai"})
  password = fields.String(required=True, metadata={"example": "********"})
  class Meta:
    unknown = EXCLUDE
  @post_load
  def post_load_handler(self, data, **kwargs):
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    return data
  @post_dump
  def post_dump_handler(self, data, **kwargs):
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    return data

class LoginTokenDto(Schema):
  access_token = fields.String()
  refresh_token = fields.String()
  class Meta:
    unknown = EXCLUDE

class RefreshAccessTokenDto(Schema):
  refresh_token = fields.String(required=True)
  class Meta:
    unknown = EXCLUDE
