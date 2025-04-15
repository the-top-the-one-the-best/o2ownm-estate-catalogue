import flask
from flask_apispec import doc, marshal_with, use_kwargs
from flask_jwt_extended import get_jwt_identity, jwt_required
from api_backend.dtos.estate_info import (
  PagedEstateInfoDto,
  QueryEstateInfoDto,
  UpsertEstateInfoDto,
  PublicEstateInfoDto,
)
from api_backend.services.estate_info import EstateInfoService
from api_backend.utils.auth_utils import check_permission
from api_backend.utils.mongo_helpers import validate_object_id
from config import Config
from constants import APITags, Permission, PermissionTargets

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
estate_info_service = EstateInfoService()

@blueprint.route("/_id/<_id>", methods=["GET"])
@doc(
  summary='get estate info by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.read,
  ),
  tags=[APITags.estate_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_info, Permission.read)
@marshal_with(PublicEstateInfoDto)
def get_by_id(_id):
  _id = validate_object_id(_id)
  result = estate_info_service.find_by_id(_id)
  return flask.jsonify(PublicEstateInfoDto().dump(result))

@blueprint.route("/query", methods=["POST"])
@doc(
  summary='query estate info by dto, use POST for complicated query body, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.read,
  ),
  tags=[APITags.estate_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required()
@check_permission(PermissionTargets.estate_customer_info, Permission.read)
@use_kwargs(QueryEstateInfoDto)
@marshal_with(PagedEstateInfoDto)
def query(**query):
  result = estate_info_service.query_by_filter(query)
  return flask.jsonify(PagedEstateInfoDto().dump(result))

@blueprint.route("/create", methods=["POST"])
@doc(
  summary='create new estate info, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.estate_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@use_kwargs(UpsertEstateInfoDto)
@marshal_with(PublicEstateInfoDto)
def create(**kwargs):
  user_id = validate_object_id(get_jwt_identity())
  created = estate_info_service.create(kwargs, user_id=user_id)
  return flask.jsonify(PublicEstateInfoDto().dump(created))

@blueprint.route("/_id/<_id>", methods=["PATCH"])
@doc(
  summary='update estate info by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.estate_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@use_kwargs(UpsertEstateInfoDto)
@marshal_with(PublicEstateInfoDto)
def update_by_id(_id, **kwargs):
  _id = validate_object_id(_id)
  user_id = validate_object_id(get_jwt_identity())
  result = estate_info_service.update_by_id(_id, kwargs, user_id=user_id)
  return flask.jsonify(PublicEstateInfoDto().dump(result))

@blueprint.route("/_id/<_id>", methods=["DELETE"])
@doc(
  summary='delete estate info by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.estate_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
def delete_by_id(_id):
  _id = validate_object_id(_id)
  user_id = validate_object_id(get_jwt_identity())
  estate_info_service.delete_by_id(validate_object_id(_id), user_id=user_id)
  return "", 204
