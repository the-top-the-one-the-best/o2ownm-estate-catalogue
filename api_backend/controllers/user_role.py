import flask
from flask_apispec import doc, marshal_with, use_kwargs
from flask_jwt_extended import get_jwt_identity, jwt_required
from api_backend.dtos.user_role import (
  PagedUserRoleDto,
  QueryUserRoleDto,
  UpsertUserRoleDto,
)
from api_backend.schemas import UserRoleSchema
from api_backend.services.user_role import UserRoleService
from api_backend.utils.auth_utils import check_permission
from api_backend.utils.mongo_helpers import validate_object_id
from config import Config
from constants import APITags, Permission, PermissionTargets

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
user_role_service = UserRoleService()

@blueprint.route("/_id/<_id>", methods=["GET"])
@doc(
  summary='get user role by _id, permission <%s:%s> required' % (
    PermissionTargets.user_role_mgmt,
    Permission.read,
  ),
  tags=[APITags.user_role_mgmt, APITags.admin],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.user_role_mgmt, Permission.read)
@marshal_with(UserRoleSchema)
def get_by_id(_id):
  _id = validate_object_id(_id)
  result = user_role_service.find_by_id(_id)
  return flask.jsonify(UserRoleSchema().dump(result))

@blueprint.route("/query", methods=["POST"])
@doc(
  summary='query user role by dto, use POST for complicated query body, permission <%s:%s> required' % (
    PermissionTargets.user_role_mgmt,
    Permission.read,
  ),
  tags=[APITags.user_role_mgmt, APITags.admin],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.user_role_mgmt, Permission.read)
@use_kwargs(QueryUserRoleDto)
@marshal_with(PagedUserRoleDto)
def query(**query):
  result = user_role_service.query_by_filter(query)
  return flask.jsonify(PagedUserRoleDto().dump(result))

@blueprint.route("/create", methods=["POST"])
@doc(
  summary='create new user role, permission <%s:%s> required' % (
    PermissionTargets.user_role_mgmt,
    Permission.write,
  ),
  tags=[APITags.user_role_mgmt, APITags.admin],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.user_role_mgmt, Permission.write)
@use_kwargs(UpsertUserRoleDto)
@marshal_with(UserRoleSchema)
def create(**kwargs):
  user_id = validate_object_id(get_jwt_identity())
  created = user_role_service.create(kwargs, user_id=user_id)
  return flask.jsonify(UserRoleSchema().dump(created))

@blueprint.route("/_id/<_id>", methods=["PATCH"])
@doc(
  summary='update user role by _id, permission <%s:%s> required' % (
    PermissionTargets.user_role_mgmt,
    Permission.write,
  ),
  tags=[APITags.user_role_mgmt, APITags.admin],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.user_role_mgmt, Permission.write)
@use_kwargs(UpsertUserRoleDto)
@marshal_with(UserRoleSchema)
def update_by_id(_id, **kwargs):
  user_id = validate_object_id(get_jwt_identity())
  result = user_role_service.update_by_id(validate_object_id(_id), kwargs, user_id=user_id)
  return flask.jsonify(UserRoleSchema().dump(result))

@blueprint.route("/_id/<_id>", methods=["DELETE"])
@doc(
  summary='delete user role by _id, permission <%s:%s> required' % (
    PermissionTargets.user_role_mgmt,
    Permission.write,
  ),
  tags=[APITags.user_role_mgmt, APITags.admin],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.user_role_mgmt, Permission.write)
def delete_by_id(_id):
  _id = validate_object_id(_id)
  user_id = validate_object_id(get_jwt_identity())
  user_role_service.delete_by_id(_id, user_id=user_id)
  return "", 204
