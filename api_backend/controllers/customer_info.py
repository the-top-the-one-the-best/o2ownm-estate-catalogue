import flask
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.customer_info import PagedCustomerInfoDto, QueryCustomerInfoDto
from api_backend.services.customer_info import CustomerInfoService

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
alumni_info_service = CustomerInfoService()

@blueprint.route("/admin/query", methods=["GET"])
@doc(
  summary='admin query alumni member info by dto',
  tags=['客戶資料', 'admin'],
)
@use_kwargs(QueryCustomerInfoDto, location="query")
@marshal_with(PagedCustomerInfoDto)
def query(**query):
  result = alumni_info_service.query_by_filter(query)
  return flask.jsonify(PagedCustomerInfoDto().dump(result))
