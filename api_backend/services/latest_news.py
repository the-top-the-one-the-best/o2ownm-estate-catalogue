import pytz
import pymongo
import werkzeug.exceptions
from api_backend.services.file_ops import FileOpsService
from config import Config
from datetime import datetime
from utils import lookup_collection, find_resources_to_remove

class LatestNewsService():
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.latestnews
    self.file_svc = FileOpsService()
    return
  
  def _find_latest_news(self, query_dto, find_one=False, find_inactive=False):
    match_filter = {}
    _now = datetime.now(pytz.UTC)
    if '_ids' in query_dto and query_dto['_ids']:
      match_filter['_id'] = {'$in': query_dto['_ids']}
    if 'creator_id' in query_dto:
      match_filter['creator_id'] = query_dto['creator_id']
    if 'updater_id' in query_dto:
      match_filter['updater_id'] = query_dto['updater_id']
    if not find_inactive:
      match_filter['start_time'] = {'$not': {'$gte': _now}}
      match_filter['end_time'] = {'$not': {'$lte': _now}}
    page_size = query_dto.get('page_size') or 20
    page_number = query_dto.get('page_number') or 1
    agg_stages = []
    if match_filter:
      agg_stages.append({'$match': match_filter})
    agg_stages.append({'$sort': {'created_at': -1}})
    agg_stages.append({'$skip': page_size * (page_number-1)})
    agg_stages.append({'$limit': page_size})

    if query_dto.get('with_user_info'):
      lookup_collection(agg_stages, 'users', 'creator_id', 'creator')
      lookup_collection(agg_stages, 'users', 'updater_id', 'updater')

    results = list(self.collection.aggregate(agg_stages))
    if find_one:
      return results[0] if results else None
    return results
  
  def create(self, uid, dto):
    dto['created_at'] = datetime.now(pytz.UTC)
    dto['updated_at'] = datetime.now(pytz.UTC)
    dto['creator_id'] = uid
    dto['updater_id'] = uid
    insert_result = self.collection.insert_one(dto)
    return self.find_by_id(insert_result.inserted_id, find_inactive=True)
  
  def delete_by_id(self, _id):
    target = self.collection.find_one_and_delete({'_id': _id})
    resource_diff = find_resources_to_remove(target, None)
    for unused_url in resource_diff:
      self.file_svc.remove_from_fs(unused_url)
    return

  def update_by_id(self, _id, uid, dto):
    dto['updated_at'] = datetime.now(pytz.UTC)
    dto['updater_id'] = uid
    target = self.collection.find_one_and_update({'_id': _id}, {'$set': dto})
    result = self.find_by_id(_id, find_inactive=True)
    resource_diff = find_resources_to_remove(target, result)
    for unused_url in resource_diff:
      self.file_svc.remove_from_fs(unused_url)
    return result

  def query_by_filter(self, query_dto, find_inactive=False):
    results = {
      "results": self._find_latest_news(query_dto, find_inactive=find_inactive),
      "page_size": query_dto.get("page_size"),
      "page_number": query_dto.get("page_number"),
    }
    return results
  
  def find_by_id(self, _id, find_inactive=False):
    match_filter = {'_id': _id}
    _now = datetime.now(pytz.UTC)
    if not find_inactive:
      match_filter['start_time'] = {'$not': {'$gte': _now}}
      match_filter['end_time'] = {'$not': {'$lte': _now}}
    agg_stages = [{'$match': match_filter}]
    lookup_collection(agg_stages, 'users', 'creator_id', 'creator')
    lookup_collection(agg_stages, 'users', 'updater_id', 'updater')  
    results = list(self.collection.aggregate(agg_stages))
    result = results[0] if results else None
    if not result:
      raise werkzeug.exceptions.NotFound
    return result
  