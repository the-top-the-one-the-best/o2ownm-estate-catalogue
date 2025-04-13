from datetime import datetime
import pymongo
import pytz
import werkzeug.exceptions
from config import Config

class EstateInfoService():
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.estateinfos

  def find_by_id(self, _id):
    match_filter = {'_id': _id}
    agg_stages = [{'$match': match_filter}]
    result = self.collection.find_one(agg_stages)
    if not result:
      raise werkzeug.exceptions.NotFound
    return result

  def create(self, dto):
    dto['created_at'] = datetime.now(pytz.UTC)
    dto['updated_at'] = datetime.now(pytz.UTC)
    insert_result = self.collection.insert_one(dto)
    return self.find_by_id(insert_result.inserted_id)
  
  def find_by_id(self, _id):
    match_filter = {'_id': _id}
    agg_stages = [{'$match': match_filter}]
    result = self.collection.find_one(agg_stages)
    if not result:
      raise werkzeug.exceptions.NotFound
    return result
