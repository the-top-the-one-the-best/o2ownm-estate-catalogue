from datetime import datetime
from bson import ObjectId
import pymongo
import pytz
import werkzeug.exceptions
from api_backend.schemas import CustomerInfoSchema
from api_backend.utils.mongo_helpers import build_mongo_index, get_district_query
from config import Config

class CustomerInfoService():
  __loaded__ = False
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.customerinfos
    self.customer_tag_collection = self.db.customertags
    self.estate_info_collection = self.db.estateinfos
    if not CustomerInfoService.__loaded__:
      CustomerInfoService.__loaded__ = True
      for index in (CustomerInfoSchema.MongoMeta.index_list):
        build_mongo_index(self.collection, index)

  def __query_by_filter__(self, query_dto):
    match_filter = {}
    if query_dto.get("estate_info_id"):
      match_filter["estate_info_id"] = query_dto["estate_info_id"]
    if type(query_dto.get("room_layouts")) is list and query_dto["room_layouts"]:
      match_filter["room_layouts"] = { "$all": query_dto["room_layouts"] }
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
    if type(query_dto.get("customer_tags")) is list and query_dto["customer_tags"]:
      match_filter["customer_tags"] = { "$all": query_dto["customer_tags"] }

    page_size = query_dto.get('page_size')
    page_number = query_dto.get('page_number')
    agg_stages = []
    matched_count = None
    if match_filter:
      agg_stages.append({"$match": match_filter})
    # check matched count
    if bool(query_dto.get("count_matched")):
      matched_count = self.collection.count_documents(match_filter)
    agg_stages.append({'$skip': page_size * (page_number-1)})
    agg_stages.append({'$limit': page_size + 1})
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
    if type(dto.get("customer_tags")) is list and dto["customer_tags"]:
      found_tags = { 
        tag["_id"] for tag in self.customer_tag_collection.find(
          { "_id": { "$in": dto["customer_tags"] }}, { "_id": 1 }
        )
      }
      provided_tags = set(dto["customer_tags"])
      tags_diff = provided_tags - found_tags
      if len(tags_diff):
        raise werkzeug.exceptions.NotFound("tags %s not found" % str(tags_diff))
    if type(dto.get("estate_info_id")) is ObjectId:
      if not self.estate_info_collection.find_one({ "_id": dto["estate_info_id"]}):
        raise werkzeug.exceptions.NotFound("estate %s not found" % str(dto["estate_info_id"]))
    inserted_id = self.collection.insert_one(dto).inserted_id
    return self.find_by_id(inserted_id)
  
  def update_by_id(self, _id, dto, user_id=None):
    dto["updated_at"] = datetime.now(pytz.UTC)
    dto["updater_id"] = user_id
    if type(dto.get("customer_tags")) is list and dto["customer_tags"]:
      found_tags = { 
        tag["_id"] for tag in self.customer_tag_collection.find(
          { "_id": { "$in": dto["customer_tags"] }}, { "_id": 1 }
        )
      }
      provided_tags = set(dto["customer_tags"])
      tags_diff = provided_tags - found_tags
      if len(tags_diff):
        raise werkzeug.exceptions.NotFound("tags %s not found" % str(tags_diff))
    if type(dto.get("estate_info_id")) is ObjectId:
      if not self.estate_info_collection.find_one({ "_id": dto["estate_info_id"]}):
        raise werkzeug.exceptions.NotFound("estate %s not found" % str(dto["estate_info_id"]))
    self.collection.find_one_and_update({"_id": _id}, {"$set": dto})
    return self.find_by_id(_id)
  
  def delete_by_id(self, _id, user_id=None):
    result = self.collection.find_one_and_delete({"_id": _id})
    if not result:
      raise werkzeug.exceptions.NotFound
    return None
