import flask
from flask_apispec import doc, marshal_with, use_kwargs
from flask_jwt_extended import get_jwt_identity
from api_backend.dtos.customer_info import (
  FilterCustomerInfoDto,
  PagedCustomerInfoDto,
  PublicCustomerInfoDto,
  QueryCustomerInfoDto,
  UpsertCustomerInfoDto,
)
from api_backend.dtos.generic import GenericMatchCountDto
from api_backend.services.customer_info import CustomerInfoService
from api_backend.utils.auth_utils import check_permission
from api_backend.utils.mongo_helpers import validate_object_id
from config import Config
from constants import APITags, Permission, PermissionTargets

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
customer_info_service = CustomerInfoService()

@blueprint.route("/_id/<_id>", methods=["GET"])
@doc(
  summary='get customer info by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.read,
  ),
  tags=[APITags.customer_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_info, Permission.read)
@marshal_with(PublicCustomerInfoDto)
def get_by_id(_id):
  _id = validate_object_id(_id)
  result = customer_info_service.find_by_id(_id)
  return flask.jsonify(PublicCustomerInfoDto().dump(result))

@blueprint.route("/query", methods=["POST"])
@doc(
  summary='query customer info by dto, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.read,
  ),
  tags=[APITags.customer_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_info, Permission.read)
@use_kwargs(QueryCustomerInfoDto)
@marshal_with(PagedCustomerInfoDto)
def query(**query):
  result = customer_info_service.query_by_filter(query)
  return flask.jsonify(PagedCustomerInfoDto().dump(result))

@blueprint.route("/count", methods=["POST"])
@doc(
  summary='count customer info by dto, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.read,
  ),
  tags=[APITags.customer_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_info, Permission.read)
@use_kwargs(FilterCustomerInfoDto)
@marshal_with(GenericMatchCountDto)
def count(**query):
  result = customer_info_service.count_by_filter(query)
  return flask.jsonify(GenericMatchCountDto().dump(result))


@blueprint.route("/create", methods=["POST"])
@doc(
  summary='create new customer info, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.customer_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@use_kwargs(UpsertCustomerInfoDto)
@marshal_with(PublicCustomerInfoDto)
def create(**kwargs):
  user_id = validate_object_id(get_jwt_identity())
  created = customer_info_service.create(kwargs, user_id=user_id)
  return flask.jsonify(PublicCustomerInfoDto().dump(created))

@blueprint.route("/_id/<_id>", methods=["PATCH"])
@doc(
  summary='update customer info by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.customer_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@use_kwargs(UpsertCustomerInfoDto)
@marshal_with(PublicCustomerInfoDto)
def update_by_id(_id, **kwargs):
  _id = validate_object_id(_id)
  user_id = validate_object_id(get_jwt_identity())
  result = customer_info_service.update_by_id(_id, kwargs, user_id=user_id)
  return flask.jsonify(PublicCustomerInfoDto().dump(result))

@blueprint.route("/_id/<_id>", methods=["DELETE"])
@doc(
  summary='delete customer info by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.customer_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
def delete_by_id(_id):
  _id = validate_object_id(_id)
  user_id = validate_object_id(get_jwt_identity())
  customer_info_service.delete_by_id(_id, user_id=user_id)
  return "", 204
