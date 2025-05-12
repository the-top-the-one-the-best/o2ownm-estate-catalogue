import flask
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.generic import GenericRankQueryDto
from api_backend.dtos.homepage_stats import EstateCustomerInfoTotalCountDto, RankedEstateInfoByCustomerInfoCount
from api_backend.services.homepage_stats import HomepageStatsService
from api_backend.utils.auth_utils import check_permission
from config import Config
from constants import APITags, Permission, PermissionTargets

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
homepage_stats_service = HomepageStatsService()

@blueprint.route("/estate_customer_info_total_count", methods=["GET"])
@doc(
  summary='get total count of estates & customer infos, permission <%s:%s> required' % (
    PermissionTargets.homepage,
    Permission.read,
  ),
  tags=[APITags.homepage_stats],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.homepage, Permission.read)
@marshal_with(EstateCustomerInfoTotalCountDto)
def get_estate_customer_info_total_count():
  result = homepage_stats_service.get_estate_customer_info_total_count()
  return flask.jsonify(EstateCustomerInfoTotalCountDto().dump(result))


@blueprint.route("/estate_rank_by_customer_info_count", methods=["GET"])
@doc(
  summary='get most popular estates ranked by customer infos, permission <%s:%s> required' % (
    PermissionTargets.homepage,
    Permission.read,
  ),
  tags=[APITags.homepage_stats],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.homepage, Permission.read)
@use_kwargs(GenericRankQueryDto, location="query")
@marshal_with(RankedEstateInfoByCustomerInfoCount(many=True))
def get_estate_rank_by_customer_info_count(**kwargs):
  query_dto = kwargs
  result = homepage_stats_service.estate_rank_by_customer_info_count(query_dto)
  return flask.jsonify(RankedEstateInfoByCustomerInfoCount(many=True).dump(result))
