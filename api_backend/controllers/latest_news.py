import flask
import werkzeug.exceptions
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.latest_news import PagedLatestNewsDto, PublicLatestNewsDto, QueryLatestNewsDto, UpsertLatestNewsDto
from api_backend.services.latest_news import LatestNewsService
from utils import validate_object_id
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity
from config import Config

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
latest_news_service = LatestNewsService()

@blueprint.route("/admin/", methods=["POST"])
@doc(
  summary='admin create new latest news',
  tags=['最新消息', 'admin'],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required()
@use_kwargs(UpsertLatestNewsDto)
@marshal_with(PublicLatestNewsDto)
def create(**kwargs):
  uid = get_jwt_identity()
  claims = get_jwt()
  if not claims['is_admin']:
    raise werkzeug.exceptions.Forbidden
  create_dto = kwargs
  created = latest_news_service.create(validate_object_id(uid), create_dto)
  return flask.jsonify(PublicLatestNewsDto().dump(created))

@blueprint.route("/admin/_id/<_id>", methods=["PATCH"])
@doc(
  summary='admin update latest news by _id',
  tags=['最新消息', 'admin'],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required()
@use_kwargs(UpsertLatestNewsDto)
@marshal_with(PublicLatestNewsDto)
def update_by_id(_id, **kwargs):
  uid = get_jwt_identity()
  claims = get_jwt()
  if not claims['is_admin']:
    raise werkzeug.exceptions.Forbidden
  update_dto = kwargs
  updated = latest_news_service.update_by_id(
    validate_object_id(_id),
    validate_object_id(uid),
    update_dto,
  )
  return flask.jsonify(PublicLatestNewsDto().dump(updated))


@blueprint.route("/admin/_id/<_id>", methods=["DELETE"])
@doc(
  summary='admin delete latest news by _id',
  tags=['最新消息', 'admin'],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required()
def delete_by_id(_id):
  claims = get_jwt()
  if not claims['is_admin']:
    raise werkzeug.exceptions.Forbidden
  updated = latest_news_service.delete_by_id(validate_object_id(_id))
  return flask.jsonify(PublicLatestNewsDto().dump(updated))

@blueprint.route("/active/query", methods=["GET"])
@doc(
  summary='query active latest news by dto',
  tags=['最新消息'],
)
@use_kwargs(QueryLatestNewsDto, location="query")
@marshal_with(PagedLatestNewsDto)
def query_active(**query):
  result = latest_news_service.query_by_filter(query)
  return flask.jsonify(PagedLatestNewsDto().dump(result))

@blueprint.route("/active/_id/<_id>", methods=["GET"])
@doc(
  summary='find active latest news by _id',
  tags=['最新消息'],
)
@marshal_with(PublicLatestNewsDto)
def get_active_by_id(_id):
  _id = validate_object_id(_id)
  result = latest_news_service.find_by_id(_id)
  return flask.jsonify(PublicLatestNewsDto().dump(result))

@blueprint.route("/admin/query", methods=["GET"])
@doc(
  summary='admin query latest news by dto',
  tags=['最新消息', 'admin'],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required()
@use_kwargs(QueryLatestNewsDto, location="query")
@marshal_with(PagedLatestNewsDto)
def admin_query(**query):
  claims = get_jwt()
  if not claims['is_admin']:
    raise werkzeug.exceptions.Forbidden
  result = latest_news_service.query_by_filter(query, find_inactive=True)
  return flask.jsonify(PagedLatestNewsDto().dump(result))

@blueprint.route("/admin/_id/<_id>", methods=["GET"])
@doc(
  summary='admin find latest news by _id',
  tags=['最新消息', 'admin'],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required()
@marshal_with(PublicLatestNewsDto)
def admin_get_by_id(_id):
  claims = get_jwt()
  if not claims['is_admin']:
    raise werkzeug.exceptions.Forbidden
  _id = validate_object_id(_id)
  result = latest_news_service.find_by_id(_id, find_inactive=True)
  return flask.jsonify(PublicLatestNewsDto().dump(result))
