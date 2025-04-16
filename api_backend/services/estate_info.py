from datetime import datetime
import pymongo
import pytz
import re
import werkzeug.exceptions
from api_backend.schemas import EstateInfoSchema
from api_backend.services.customer_info import CustomerInfoService
from api_backend.utils.mongo_helpers import build_mongo_index, get_district_query
from config import Config

class EstateInfoService():
  __loaded__ = False
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.estateinfos
    self.customer_info_service = CustomerInfoService()
    if not EstateInfoService.__loaded__:
      EstateInfoService.__loaded__ = True
      for index in (EstateInfoSchema.MongoMeta.index_list):
        build_mongo_index(self.collection, index)

  def __query_by_filter__(self, query_dto):
    match_filter = {}
    if type(query_dto.get("_ids")) is list and len(query_dto["_ids"]):
      match_filter["_id"] = {"$in": query_dto["_ids"]}
    if type(query_dto.get("name")) is str and query_dto["name"]:
      pattern = ".*%s.*" % (query_dto["name"], )
      pattern_regex = re.compile(pattern)
      match_filter["name"] = pattern_regex
    if type(query_dto.get("room_layouts")) is list and query_dto["room_layouts"]:
      match_filter["room_layouts"] = { "$all": query_dto["room_layouts"] }
    if type(query_dto.get("estate_tags")) is list and query_dto["estate_tags"]:
      match_filter["estate_tags"] = { "$all": query_dto["estate_tags"] }
    if type(query_dto.get("room_size")) is dict and query_dto["room_size"]:
      size_query = {}
      if query_dto["room_size"].get("size_max"):
        size_query["size_max"] = { "$lte": query_dto["room_size"]["size_max"] }
      if query_dto["room_size"].get("size_min"):
        size_query["size_min"] = { "$gte": query_dto["room_size"]["size_min"] }
      match_filter["room_sizes"] = { "$elemMatch": size_query }
    if type(query_dto.get("districts")) is list and query_dto["districts"]:
      match_filter["$or"] = [
        get_district_query(pairs) for pairs in query_dto["districts"]
      ]

    page_size = query_dto.get("page_size")
    page_number = query_dto.get("page_number")
    agg_stages = []
    matched_count = None
    if match_filter:
      agg_stages.append({"$match": match_filter})
    # check matched count
    if bool(query_dto.get("count_matched")):
      matched_count = self.collection.count_documents(match_filter)
    agg_stages.append({"$sort": {"created_at": -1, "_id": 1}})
    agg_stages.append({"$skip": page_size * (page_number - 1)})
    agg_stages.append({"$limit": page_size + 1})
    results = list(self.collection.aggregate(agg_stages))
    return results[:page_size], bool(len(results) > page_size), matched_count

  def find_by_id(self, _id):
    result = self.collection.find_one({"_id": _id})
    if not result:
      raise werkzeug.exceptions.NotFound
    return result

  def query_by_filter(self, query_dto):
    paged_result, has_more, matched_count = self.__query_by_filter__(query_dto)
    result = {
      "results": paged_result,
      "has_more": has_more,
      "page_size": query_dto.get("page_size"),
      "page_number": query_dto.get("page_number"),
    }
    if not matched_count is None:
      result["matched_count"] = matched_count
    return result
  
  def create(self, dto, user_id=None):
    dto["created_at"] = datetime.now(pytz.UTC)
    dto["updated_at"] = datetime.now(pytz.UTC)
    dto["creator_id"] = user_id
    dto["updater_id"] = user_id
    inserted_id = self.collection.insert_one(dto).inserted_id
    return self.find_by_id(inserted_id)

  def update_by_id(self, _id, dto, user_id=None):
    dto["updated_at"] = datetime.now(pytz.UTC)
    dto["updater_id"] = user_id
    self.collection.find_one_and_update({"_id": _id}, {"$set": dto})
    result = self.find_by_id(_id)
    return self.find_by_id(result)
    
  def delete_by_id(self, _id, user_id=None):
    result = self.collection.find_one_and_delete({"_id": _id})
    if not result:
      raise werkzeug.exceptions.NotFound
    # delete customer info tied to this estate
    self.customer_info_service.collection.delete_many(
      { "estate_info_id": _id }
    )
    return None
