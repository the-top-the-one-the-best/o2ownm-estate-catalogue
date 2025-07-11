from datetime import datetime
import re
from bson import ObjectId
import pymongo
import pytz
import werkzeug.exceptions
from api_backend.schemas import (
  CustomerInfoDraftSchema,
  CustomerInfoErrorSchema,
  CustomerInfoSchema,
)
from api_backend.dtos.customer_info import default_customer_info_sort_option
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
    self.draft_collection = self.db.customerinfodrafts
    self.import_error_collection = self.db.customerinfoimporterrors
    self.customer_tag_collection = self.db.customertags
    self.estate_info_collection = self.db.estateinfos
    if not CustomerInfoService.__loaded__:
      CustomerInfoService.__loaded__ = True
      for index in (CustomerInfoSchema.MongoMeta.index_list):
        build_mongo_index(self.collection, index)
      for index in CustomerInfoDraftSchema.MongoMeta.index_list:
        build_mongo_index(self.draft_collection, index)
      for index in (CustomerInfoErrorSchema.MongoMeta.index_list):
        build_mongo_index(self.import_error_collection, index)
        
  def __build_match_filter__(self, query_dto):
    match_filter = {}
    if type(query_dto.get("name")) is str and query_dto["name"]:
      pattern = ".*%s.*" % (query_dto["name"], )
      pattern_regex = re.compile(pattern, re.IGNORECASE)
      match_filter["name"] = pattern_regex
    if type(query_dto.get("phone")) is str and query_dto["phone"]:
      pattern = ".*%s.*" % (query_dto["phone"], )
      pattern_regex = re.compile(pattern, re.IGNORECASE)
      match_filter["phone"] = pattern_regex
    if type(query_dto.get("email")) is str and query_dto["email"]:
      pattern = ".*%s.*" % (query_dto["email"], )
      pattern_regex = re.compile(pattern, re.IGNORECASE)
      match_filter["email"] = pattern_regex
    if type(query_dto.get("estate_info_ids")) is list and query_dto.get("estate_info_ids"):
      match_filter["estate_info_id"] = { "$in": query_dto["estate_info_ids"] }
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
    return match_filter

  def count_by_filter(self, query_dto, grouped_fields=["phone"]):
    match_filter = self.__build_match_filter__(query_dto)
    agg_stages = []
    if match_filter:
      agg_stages.append({"$match": match_filter})
    facet_stage = { "matched_count": [ { "$count": "count" } ] }
    distinct_flag = type(grouped_fields) is list and len(grouped_fields)
    if distinct_flag:
      grouped_fields = [
        field.strip() if field.strip().startswith("$") else "$" + field.strip()
        for field in grouped_fields if type(field) is str and field.strip()
      ]
      facet_stage["distinct_matched_count"] = [
        { "$group": { "_id": grouped_fields } },
        { "$count": "count" },
      ]
    agg_stages.append({ "$facet": facet_stage})
    project_stage = {
      "matched_count": { "$ifNull": [ { "$arrayElemAt": ["$matched_count.count", 0] }, 0 ] },
    }
    if distinct_flag:
      project_stage["distinct_matched_count"] = {
        "$ifNull": [ { "$arrayElemAt": ["$distinct_matched_count.count", 0] }, 0 ]
      }
    agg_stages.append({ "$project": project_stage})

    results = list(self.collection.aggregate(agg_stages))
    result = results[0] if results else {}
    result["grouped_fields"] = grouped_fields if distinct_flag else []
    if type(result.get("matched_count")) is int and not result.get("distinct_matched_count"):
      result["distinct_matched_count"] = result["matched_count"]
    return result

  def find_by_id(self, _id):
    result = self.collection.find_one({"_id": _id})
    if not result:
      raise werkzeug.exceptions.NotFound
    return result
  
  def query_export_cursor(self, query_dto, grouped_fields=["phone"]):
    match_filter = self.__build_match_filter__(query_dto)
    agg_stages = []
    if match_filter:
      agg_stages.append({ "$match": match_filter })
    sort_fields = {}
    if type(grouped_fields) is list and grouped_fields:
      for grouped_field in grouped_fields:
        sort_fields[grouped_field] = 1
    sort_fields["updated_at"] = -1
    sort_fields["created_at"] = -1
    agg_stages.append({ "$sort": sort_fields })
    if type(grouped_fields) is list and grouped_fields:
      agg_stages.append({
        "$group": {
          "_id": [
            field.strip() if field.strip().startswith("$") else "$" + field.strip()
            for field in grouped_fields if type(field) is str and field.strip()
          ],
          "doc": { "$first": "$$ROOT" },
        }
      })
      agg_stages.append({ "$replaceRoot": { "newRoot": "$doc" }})
    return self.collection.aggregate(agg_stages)

  def query_by_filter(self, query_dto):
    # paged_result, has_more, matched_count = self.__query_by_filter__(query_dto)
    match_filter = self.__build_match_filter__(query_dto)
    page_size = query_dto.get("page_size")
    page_number = query_dto.get("page_number")
    sort_options = query_dto.get("sort_options") or default_customer_info_sort_option

    agg_stages = []
    matched_count = None
    if match_filter:
      agg_stages.append({"$match": match_filter})
    # check matched count
    if bool(query_dto.get("count_matched")):
      matched_count = self.collection.count_documents(match_filter)
    
    if sort_options.get("field") and sort_options.get("order"):
      agg_stages.append({ "$sort": { sort_options.get("field"): sort_options.get("order"), "_id": -1 }})
    
    agg_stages.append({'$skip': page_size * (page_number-1)})
    agg_stages.append({'$limit': page_size + 1})
    results = list(self.collection.aggregate(agg_stages))
    result = {
      "results": results[:page_size],
      "has_more": bool(len(results) > page_size),
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
    if type(dto.get("estate_info_id")) is ObjectId:
      if not self.estate_info_collection.find_one({ "_id": dto["estate_info_id"]}):
        raise werkzeug.exceptions.NotFound("estate %s not found" % str(dto["estate_info_id"]))
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
