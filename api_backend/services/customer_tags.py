import pymongo
import re
import werkzeug.exceptions
from api_backend.schemas import CustomerTagSchema
from api_backend.utils.mongo_helpers import build_mongo_index
from config import Config

class CustomerTagsService():
  __loaded__ = False
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.customertags
    self.customer_info_collection = self.db.customerinfos
    if not CustomerTagsService.__loaded__:
      CustomerTagsService.__loaded__ = True
      for index in (CustomerTagSchema.MongoMeta.index_list):
        build_mongo_index(self.collection, index)

  def __query_by_filter__(self, query_dto):
    match_filter = {}
    if type(query_dto.get("name")) is str and query_dto["name"]:
      pattern = ".*%s.*" % (query_dto["name"], )
      pattern_regex = re.compile(pattern, re.IGNORECASE)
      match_filter["name"] = pattern_regex
    if type(query_dto.get("is_frequently_used")) is bool and query_dto["is_frequently_used"]:
      match_filter["is_frequently_used"] = True
    page_size = query_dto.get("page_size")
    page_number = query_dto.get("page_number")
    agg_stages = []
    matched_count = None
    if match_filter:
      agg_stages.append({"$match": match_filter})
    # check matched count
    if bool(query_dto.get("count_matched")):
      matched_count = self.collection.count_documents(match_filter)
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
    if self.collection.find_one({ "name": dto.get("name")}):
      raise werkzeug.exceptions.Conflict("duplicated tag %s" % (dto["name"], ))
    inserted_id = self.collection.insert_one(dto).inserted_id
    return self.find_by_id(inserted_id)

  def update_by_id(self, _id, dto, user_id=None):
    if type(dto.get("name")) is str:
      if self.collection.find_one({ "name": dto["name"], "_id": { "$ne": _id } }):
        raise werkzeug.exceptions.Conflict("duplicated tag %s" % (dto["name"], ))
    self.collection.find_one_and_update({"_id": _id}, {"$set": dto})
    return self.find_by_id(_id)
    
  def delete_by_id(self, _id, user_id=None):
    result = self.collection.find_one_and_delete({"_id": _id})
    if not result:
      raise werkzeug.exceptions.NotFound
    # update customer info tags field
    from api_backend.services.customer_info import CustomerInfoService
    customer_service = CustomerInfoService()
    customer_service.collection.update_many(
      { "customer_tags": _id },
      { "$pull": { "customer_tags": _id } },
    )
    customer_service.draft_collection.update_many(
      { "customer_tags": _id },
      { "$pull": { "customer_tags": _id } },
    )
    return None
