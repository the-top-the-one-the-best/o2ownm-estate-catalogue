from datetime import datetime
import pymongo
import re
import pytz
import werkzeug.exceptions
from config import Config

class UserRoleService():
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.userroles

  def __query_by_filter__(self, query_dto):
    match_filter = {}
    if type(query_dto.get("name")) is str and query_dto["name"]:
      pattern = ".*%s.*" % (query_dto["name"], )
      pattern_regex = re.compile(pattern, re.IGNORECASE)
      match_filter["name"] = pattern_regex
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
    if self.collection.find_one({ "name": dto.get("name") }):
      raise werkzeug.exceptions.Conflict("duplicated name %s" % (dto["name"], ))
    dto["creator_id"] = user_id
    dto["updater_id"] = user_id
    dto["created_at"] = datetime.now(pytz.UTC)
    dto["updated_at"] = datetime.now(pytz.UTC)
    inserted_id = self.collection.insert_one(dto).inserted_id
    return self.find_by_id(inserted_id)

  def update_by_id(self, _id, dto, user_id=None):
    if type(dto.get("name")) is str:
      if self.collection.find_one({ "name": dto["name"], "_id": { "$ne": _id } }):
        raise werkzeug.exceptions.Conflict("duplicated name %s" % (dto["name"], ))
      
    dto["updater_id"] = user_id
    dto["updated_at"] = datetime.now(pytz.UTC)
    self.collection.find_one_and_update({"_id": _id}, {"$set": dto})
    return self.find_by_id(_id)
    
  def delete_by_id(self, _id, user_id=None):
    result = self.collection.find_one_and_delete({"_id": _id})
    if not result:
      raise werkzeug.exceptions.NotFound
    return None
