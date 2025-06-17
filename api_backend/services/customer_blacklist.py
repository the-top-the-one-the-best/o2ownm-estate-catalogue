from datetime import datetime
import re
import pymongo
import pytz
import werkzeug.exceptions
from api_backend.schemas import (
  CustomerBlacklistDraftSchema,
  CustomerBlacklistErrorSchema,
  CustomerBlacklistSchema,
)
from api_backend.utils.mongo_helpers import build_mongo_index
from config import Config

class CustomerBlacklistService():
  __loaded__ = False
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.customerblacklists
    self.draft_collection = self.db.customerblacklistdrafts
    self.import_error_collection = self.db.customerblacklistimporterrors
    if not CustomerBlacklistService.__loaded__:
      CustomerBlacklistService.__loaded__ = True
      for index in (CustomerBlacklistSchema.MongoMeta.index_list):
        build_mongo_index(self.collection, index)
      for index in CustomerBlacklistDraftSchema.MongoMeta.index_list:
        build_mongo_index(self.draft_collection, index)
      for index in (CustomerBlacklistErrorSchema.MongoMeta.index_list):
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
    inserted_id = self.collection.insert_one(dto).inserted_id
    return self.find_by_id(inserted_id)
  
  def update_by_id(self, _id, dto, user_id=None):
    dto["updated_at"] = datetime.now(pytz.UTC)
    dto["updater_id"] = user_id
    self.collection.find_one_and_update({"_id": _id}, {"$set": dto})
    return self.find_by_id(_id)
  
  def delete_by_id(self, _id, user_id=None):
    result = self.collection.find_one_and_delete({"_id": _id})
    if not result:
      raise werkzeug.exceptions.NotFound
    return None
