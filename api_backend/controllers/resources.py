import flask
import os
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.resources import QueryDistrictByNameSchema
from api_backend.schemas import TaiwanAdministrativeDistrictSchema
from api_backend.services.resources import ResourceService
from constants import APITags

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)

resource_service = ResourceService()
@doc(summary="get l1 TW administrative district by names", tags=[APITags.resources])
@blueprint.route("/tw_administrative_districts/query", methods=["GET"])
@use_kwargs(QueryDistrictByNameSchema, location="query")
@marshal_with(TaiwanAdministrativeDistrictSchema(many=True))
def get_tw_administrative_districts_by_name(**kwargs):
  targets = resource_service.get_l1_tw_administrative_districts(kwargs)
  return flask.jsonify(TaiwanAdministrativeDistrictSchema(many=True).dump(targets))

@doc(summary="get estate customer xlsx import template", tags=[APITags.resources])
@blueprint.route("/estate_customer_xlsx_import_template", methods=["GET"])
def get_estate_customer_xlsx_import_template():
  file_path = os.path.join("resources", "estate_customer_info_import_template.xlsx")
  print ('####', file_path)
  return flask.send_file(file_path, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@doc(summary="get estate customer blacklist import template", tags=[APITags.resources])
@blueprint.route("/estate_customer_blacklist_xlsx_import_template", methods=["GET"])
def get_estate_customer_blacklist_xlsx_import_template():
  file_path = os.path.join("resources", "customer_blacklist_import_template.xlsx")
  print ('####', file_path)
  return flask.send_file(file_path, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
