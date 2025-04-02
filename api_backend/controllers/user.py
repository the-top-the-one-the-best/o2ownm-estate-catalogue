import flask
import werkzeug.exceptions
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.generic import GeneralInsertIdDto
from api_backend.dtos.user import (
  CreateUserDto,
  CredentialDto,
  LoginTokenDto,
  PublicUserDto,
  RefreshAccessTokenDto,
  RequestResetPasswordDto,
  ResetPasswordDto,
  UpdatePasswordDto,
  UpdateUserDto,
)
from utils import admins_only, validate_object_id
from flask_jwt_extended import decode_token, get_jwt, jwt_required, get_jwt_identity
from api_backend.services.user import UserService
from config import Config

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
user_service = UserService()

@blueprint.route("/login", methods=["POST"])
@doc(
  summary='login with credential',
  tags=['帳戶']
)
@use_kwargs(CredentialDto)
@marshal_with(LoginTokenDto)
def login(**kwargs):
  credential_dto = kwargs
  return flask.jsonify(
    LoginTokenDto().dump(user_service.login(credential_dto))
  )

@blueprint.route("/register", methods=["POST"])
@doc(
  summary='register with credential',
  tags=['帳戶']
)
@use_kwargs(CredentialDto)
@marshal_with(GeneralInsertIdDto)
def register(**kwargs):
  credential_dto = kwargs
  return flask.jsonify(
    GeneralInsertIdDto().dump(user_service.register(credential_dto))
  )

@blueprint.route("/logout", methods=["POST"])
@jwt_required()
@doc(
  summary='logout and disable token',
  tags=['帳戶'],
  security=[Config.JWT_SECURITY_OPTION],
)
@marshal_with("", "204")
def logout():
  raw_jwt = get_jwt()
  user_service.logout(raw_jwt)
  return '', 204

@blueprint.route("/profile", methods=["GET"])
@jwt_required()
@doc(
  summary='get who I am',
  tags=['帳戶'],
  security=[Config.JWT_SECURITY_OPTION]
)
@marshal_with(PublicUserDto)
def whoami():
  uid = get_jwt_identity()
  return flask.jsonify(
    PublicUserDto().dump(user_service.get_profile_by_uid(validate_object_id(uid)))
  )

@blueprint.route("/profile", methods=["PATCH"])
@jwt_required()
@doc(
  summary='update profile',
  tags=['帳戶'],
  security=[Config.JWT_SECURITY_OPTION]
)
@use_kwargs(UpdateUserDto)
@marshal_with(PublicUserDto)
def update_profile(**kwargs):
  uid = get_jwt_identity()
  update_dto = kwargs
  return flask.jsonify(
    PublicUserDto().dump(user_service.update_profile(validate_object_id(uid), update_dto))
  )

@blueprint.route("/password", methods=["PATCH"])
@jwt_required()
@doc(
  sumamry='change password',
  tags=['帳戶'],
  security=[Config.JWT_SECURITY_OPTION]
)
@use_kwargs(UpdatePasswordDto)
def update_password(**kwargs):
  update_pwd_dto = kwargs
  uid = get_jwt_identity()
  user_service.update_password(validate_object_id(uid), update_pwd_dto)
  return "", 204

@blueprint.route("/reset_password_request", methods=["POST"])
@doc(
  sumamry='request to reset password',
  tags=['帳戶'],
)
@use_kwargs(RequestResetPasswordDto)
def request_password_reset(**kwargs):
  reset_pwd_dto = kwargs
  user_service.request_password_reset_email(reset_pwd_dto)
  return "", 204

@blueprint.route("/reset_password/event_id/<event_id>", methods=["POST"])
@doc(
  sumamry='reset password with passphrase',
  tags=['帳戶'],
)
@use_kwargs(ResetPasswordDto)
def reset_password(event_id, **kwargs):
  reset_pwd_dto = kwargs
  user_service.reset_password_with_event_id(
    validate_object_id(event_id),
    reset_pwd_dto,
  )
  return "", 204

@blueprint.route("/refresh", methods=["GET"])
@doc(
  summary='refresh credential access token in header',
  tags=['帳戶'],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required(refresh=True)
@marshal_with(LoginTokenDto)
def refresh_access_token():
  uid = get_jwt_identity()
  return flask.jsonify(
    LoginTokenDto().dump(
      user_service.refresh_access_token(validate_object_id(uid))
    )
  )

@blueprint.route("/refresh", methods=["POST"])
@doc(
  summary='refresh credential access token in body',
  tags=['帳戶'],
)
@use_kwargs(RefreshAccessTokenDto)
@marshal_with(LoginTokenDto)
def refresh_access_token_in_body(**kwargs):
  data = kwargs
  if not data or "refresh_token" not in data:
    raise werkzeug.exceptions.BadRequest('refresh_token required')
  refresh_token = data["refresh_token"]
  try:
    decoded_token = decode_token(refresh_token)
    uid = decoded_token[Config.JWT_IDENTITY_CLAIM]
    return flask.jsonify(
      LoginTokenDto().dump(
        user_service.refresh_access_token(validate_object_id(uid))
      )
    )
  except:
    raise werkzeug.exceptions.Unauthorized('invalid refresh token')

@blueprint.route("/admin/create_account", methods=["POST"])
@doc(
  summary='admin create system account',
  tags=['ADMIN'],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required()
@admins_only()
@use_kwargs(CreateUserDto)
@marshal_with(PublicUserDto)
def admin_create_system_account(**kwargs):
  uid = get_jwt_identity()
  return flask.jsonify(
    PublicUserDto().dump(
      user_service.admin_create_user(uid, kwargs)
    )
  )
