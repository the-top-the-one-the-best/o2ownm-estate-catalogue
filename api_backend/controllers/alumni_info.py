import flask
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.alumni_info import PagedAlumniInfoDto, QueryAlumniInfoDto
from api_backend.services.alumni_info import AlumniInfoService
from flask_jwt_extended import get_jwt, jwt_required

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
alumni_info_service = AlumniInfoService()

@blueprint.route("/admin/query", methods=["GET"])
@doc(
  summary='admin query alumni member info by dto',
  tags=['校友人員資料', 'admin'],
)
@use_kwargs(QueryAlumniInfoDto, location="query")
@marshal_with(PagedAlumniInfoDto)
def query(**query):
  result = alumni_info_service.query_by_filter(query)
  return flask.jsonify(PagedAlumniInfoDto().dump(result))
