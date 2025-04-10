import pymongo
import bson
import pytz
from datetime import datetime, timedelta
from constants import AuthEventTypes, DataTargets
from config import Config

class LogService():
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.auth_log_collection = self.db.authlogs
    return
  
  def count_auth_log_events(
    self,
    uid: bson.ObjectId=None,
    event_type: AuthEventTypes=None,
    target_id: bson.ObjectId=None,
    track_period=timedelta(days=1)
  ):
    filter = {'created_at': {'gte': datetime.now(pytz.UTC) - track_period}}
    if uid:
      filter['user_id'] = uid
    if event_type:
      filter['event_type'] = event_type
    if target_id:
      filter['target_id'] = target_id
    return self.auth_log_collection.count_documents(filter)

  def log_auth_events(
    self, 
    uid: bson.ObjectId, 
    event_type: AuthEventTypes,
    target_id: bson.ObjectId=None,
    target_type: DataTargets=None,
    new_data=None,
  ):
    log = {
      "user_id": uid,
      "event_type": event_type,
      "created_at": datetime.now(pytz.UTC),
    }
    if target_id:
      log["target_id"] = target_id
      log["target_type"] = target_type
      
    if new_data:
      log["event_details"] = { "new_data": new_data }
    self.auth_log_collection.insert_one(log)
    return
  