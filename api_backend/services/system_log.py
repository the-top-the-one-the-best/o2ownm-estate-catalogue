import pymongo
import bson
import pytz
from datetime import datetime, timedelta
from api_backend.schemas import SystemLogSchema
from api_backend.utils.mongo_helpers import build_mongo_index, get_mongo_period
from constants import AuthEventTypes, DataTargets
from config import Config
import werkzeug.exceptions

class SystemLogService():
  __loaded__ = False
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.systemlogs
    if not SystemLogService.__loaded__:
      SystemLogService.__loaded__ = True
      for index in (SystemLogSchema.MongoMeta.index_list):
        build_mongo_index(self.collection, index)

  def count_auth_log_events(
    self,
    user_id: bson.ObjectId=None,
    event_type: AuthEventTypes=None,
    target_id: bson.ObjectId=None,
    track_period=timedelta(days=1)
  ):
    filter = {'created_at': {'gte': datetime.now(pytz.UTC) - track_period}}
    if user_id:
      filter['user_id'] = user_id
    if event_type:
      filter['event_type'] = event_type
    if target_id:
      filter['target_id'] = target_id
    return self.collection.count_documents(filter)

  def __query_by_filter__(self, query_dto):
    match_filter = {}
    if type(query_dto.get("user_id")) is bson.ObjectId:
      match_filter["user_id"] = query_dto["user_id"]
    if type(query_dto.get("target_id")) is bson.ObjectId:
      match_filter["target_id"] = query_dto["target_id"]
    if type(query_dto.get("target_types")) is list and query_dto["target_types"]:
      match_filter["target_type"] = { "$in": query_dto["target_types"] }
    if type(query_dto.get("event_types")) is list and query_dto["event_types"]:
      match_filter["event_types"] = { "$in": query_dto["event_types"] }
      
    created_at_interval = get_mongo_period(query_dto.get("start_time"), query_dto.get("end_time"))
    if created_at_interval:
      match_filter["created_at"] = created_at_interval

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
    print (result)
    return result
  
  def log_auth_events(
    self, 
    user_id: bson.ObjectId, 
    event_type: AuthEventTypes,
    target_id: bson.ObjectId=None,
    target_type: DataTargets=None,
    event_data=None,
  ):
    log = {
      "user_id": user_id,
      "event_type": event_type,
      "created_at": datetime.now(pytz.UTC),
    }
    if target_id:
      log["target_id"] = target_id
      log["target_type"] = target_type
      
    if event_data:
      log["event_details"] = { "new_data": event_data }
    self.collection.insert_one(log)
    return
  