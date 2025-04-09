import flask
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.customer_info import PagedCustomerInfoDto, QueryCustomerInfoDto
from api_backend.services.customer_info import CustomerInfoService
from constants import APITags

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
customer_info_service = CustomerInfoService()

@blueprint.route("/query", methods=["GET"])
@doc(
  summary='query customer info by dto',
  tags=[APITags.customer_info],
)
@use_kwargs(QueryCustomerInfoDto, location="query")
@marshal_with(PagedCustomerInfoDto)
def query(**query):
  result = customer_info_service.query_by_filter(query)
  return flask.jsonify(PagedCustomerInfoDto().dump(result))
