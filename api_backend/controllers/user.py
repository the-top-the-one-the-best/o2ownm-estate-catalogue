import flask
import werkzeug.exceptions
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.generic import GeneralInsertIdDto, GeneralPagedQueryDto
from api_backend.dtos.user import (
  CreateUserDto,
  CredentialDto,
  LoginTokenDto,
  PagedPublicUserDto,
  PublicUserDto,
  RefreshAccessTokenDto,
  RequestResetPasswordDto,
  ResetPasswordDto,
  UpdatePasswordDto,
  UpdateUserDto,
  UpdateUserPermissionDto,
)
from api_backend.utils.auth_utils import admins_only, check_permission
from api_backend.utils.mongo_helpers import validate_object_id
from constants import APITags, PermissionTargets, Permission
from flask_jwt_extended import decode_token, get_jwt, jwt_required, get_jwt_identity
from api_backend.services.user import UserService
from config import Config

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
user_service = UserService()

@blueprint.route("/login", methods=["POST"])
@doc(
  summary='login with credential',
  tags=[APITags.user]
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
  tags=[APITags.user]
)
@use_kwargs(CredentialDto)
@marshal_with(GeneralInsertIdDto)
def register(**kwargs):
  raise werkzeug.exceptions.Locked("API disabled intentionally")
  credential_dto = kwargs
  return flask.jsonify(
    GeneralInsertIdDto().dump(user_service.register(credential_dto))
  )

@blueprint.route("/logout", methods=["POST"])
@jwt_required()
@doc(
  summary='logout and disable token',
  tags=[APITags.user],
  security=[Config.JWT_SECURITY_OPTION],
)
@marshal_with("", "204")
def logout():
  raw_jwt = get_jwt()
  user_service.logout(raw_jwt)
  return '', 204

@blueprint.route("/profile/mine", methods=["GET"])
@jwt_required()
@doc(
  summary='get who I am',
  tags=[APITags.user],
  security=[Config.JWT_SECURITY_OPTION]
)
@marshal_with(PublicUserDto)
def whoami():
  user_id = get_jwt_identity()
  return flask.jsonify(
    PublicUserDto().dump(user_service.get_profile_by_user_id(validate_object_id(user_id)))
  )

@blueprint.route("/profile/mine", methods=["PATCH"])
@jwt_required()
@doc(
  summary='update profile',
  tags=[APITags.user],
  security=[Config.JWT_SECURITY_OPTION]
)
@use_kwargs(UpdateUserDto)
@marshal_with(PublicUserDto)
def update_my_profile(**kwargs):
  user_id = get_jwt_identity()
  update_dto = kwargs
  return flask.jsonify(
    PublicUserDto().dump(
      user_service.update_profile_by_user_id(validate_object_id(user_id), update_dto)
    )
  )

@blueprint.route("/profile/query", methods=["POST"])
@check_permission(PermissionTargets.user_mgmt, Permission.read)
@doc(
  summary='query users, permission <%s:%s> required' % (PermissionTargets.user_mgmt, Permission.read),
  tags=[APITags.user, APITags.admin],
  security=[Config.JWT_SECURITY_OPTION]
)
@use_kwargs(GeneralPagedQueryDto)
@marshal_with(PagedPublicUserDto)
def get_users(**kwargs):
  return flask.jsonify(
    PagedPublicUserDto().dump(user_service.query_by_filter(kwargs))
  )

@blueprint.route("/profile/_id/<user_id>", methods=["GET"])
@check_permission(PermissionTargets.user_mgmt, Permission.read)
@doc(
  summary='get user by user_id, permission <%s:%s> required' % (PermissionTargets.user_mgmt, Permission.read),
  tags=[APITags.user, APITags.admin],
  security=[Config.JWT_SECURITY_OPTION]
)
@marshal_with(PublicUserDto)
def get_user_by_id(user_id):
  return flask.jsonify(
    PublicUserDto().dump(
      user_service.get_profile_by_user_id(validate_object_id(user_id))
    )
  )

@blueprint.route("/profile/_id/<user_id>", methods=["PATCH"])
@check_permission(PermissionTargets.user_mgmt, Permission.write)
@doc(
  summary='update user by user_id, required permission <%s:%s>' % (PermissionTargets.user_mgmt, Permission.write),
  tags=[APITags.user, APITags.admin],
  security=[Config.JWT_SECURITY_OPTION]
)
@use_kwargs(UpdateUserDto)
@marshal_with(PublicUserDto)
def update_user_by_id(user_id, **kwargs):
  return flask.jsonify(
    PublicUserDto().dump(
      user_service.update_profile_by_user_id(
        validate_object_id(user_id),
        kwargs,
        run_user_id=validate_object_id(get_jwt_identity()),
      )
    )
  )

@blueprint.route("/role/_id/<user_id>", methods=["PATCH"])
@check_permission(PermissionTargets.user_mgmt, Permission.write)
@doc(
  summary='update user roles by user_id, required permission <%s:%s>' % (PermissionTargets.user_role_mgmt, Permission.full),
  tags=[APITags.user, APITags.admin],
  security=[Config.JWT_SECURITY_OPTION]
)
@use_kwargs(UpdateUserPermissionDto)
@marshal_with(PublicUserDto)
def update_user_roles_by_id(user_id, **kwargs):
  return flask.jsonify(
    PublicUserDto().dump(
      user_service.update_permissions_by_user_id(
        validate_object_id(user_id),
        kwargs,
        run_user_id=validate_object_id(get_jwt_identity()),
      )
    )
  )

@blueprint.route("/password", methods=["PATCH"])
@jwt_required()
@doc(
  summary='change password',
  tags=[APITags.user],
  security=[Config.JWT_SECURITY_OPTION]
)
@use_kwargs(UpdatePasswordDto)
def update_password(**kwargs):
  update_pwd_dto = kwargs
  user_id = get_jwt_identity()
  user_service.update_password(
    validate_object_id(user_id),
    update_pwd_dto,
    check_old_pwd=True,
  )
  return "", 204

@blueprint.route("/reset_password_request", methods=["POST"])
@doc(
  summary='request to reset password',
  tags=[APITags.user],
)
@use_kwargs(RequestResetPasswordDto)
def request_password_reset(**kwargs):
  reset_pwd_dto = kwargs
  user_service.request_password_reset_email(reset_pwd_dto)
  return "", 204

@blueprint.route("/reset_password/event_id/<event_id>", methods=["POST"])
@doc(
  summary='reset password with passphrase',
  tags=[APITags.user],
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
  tags=[APITags.user],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required(refresh=True)
@marshal_with(LoginTokenDto)
def refresh_access_token():
  user_id = get_jwt_identity()
  return flask.jsonify(
    LoginTokenDto().dump(
      user_service.refresh_access_token(validate_object_id(user_id))
    )
  )

@blueprint.route("/refresh", methods=["POST"])
@doc(
  summary='refresh credential access token in body',
  tags=[APITags.user],
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
    user_id = decoded_token[Config.JWT_IDENTITY_CLAIM]
    return flask.jsonify(
      LoginTokenDto().dump(
        user_service.refresh_access_token(validate_object_id(user_id))
      )
    )
  except:
    raise werkzeug.exceptions.Unauthorized('invalid refresh token')

@blueprint.route("/admin/create_account", methods=["POST"])
@doc(
  summary='admin create system account',
  tags=[APITags.admin],
  security=[Config.JWT_SECURITY_OPTION],
)
@admins_only()
@use_kwargs(CreateUserDto)
@marshal_with(PublicUserDto)
def admin_create_system_account(**kwargs):
  user_id = get_jwt_identity()
  return flask.jsonify(
    PublicUserDto().dump(
      user_service.admin_create_user(validate_object_id(user_id), kwargs)
    )
  )

@blueprint.route("/_id/<_id>", methods=["DELETE"])
@doc(
  summary='delete user by _id, permission <%s:%s> required' % (
    PermissionTargets.user_mgmt,
    Permission.write,
  ),
  tags=[APITags.user, APITags.admin],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.user_mgmt, Permission.write)
def delete_by_id(_id):
  _id = validate_object_id(_id)
  user_id = validate_object_id(get_jwt_identity())
  user_service.delete_by_id(_id, user_id=user_id)
  return "", 204
