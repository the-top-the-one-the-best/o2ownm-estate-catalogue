import pymongo
import bson
import pytz
from datetime import datetime, timedelta
from api_backend.schemas import SystemLogSchema
from api_backend.utils.mongo_helpers import build_mongo_index, get_mongo_period, lookup_collection
from constants import AuthEventTypes, DataTargets
from config import Config
import werkzeug.exceptions

class HomepageStatsService():
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.estate_info_collection = self.db.estateinfos
    self.customer_info_collection = self.db.customerinfos

  def get_estate_customer_info_total_count(self):
    return {
      "estate_info_count": self.estate_info_collection.count_documents({}),
      "customer_info_count": self.customer_info_collection.count_documents({}),
    }

  def estate_rank_by_customer_info_count(self, query_dto):
    limit = query_dto.get("limit")
    agg_stages = [
      { "$match": { "estate_info_id": { "$ne": None } } },
      { "$group": { "_id": "$estate_info_id", "customer_info_count": { "$sum": 1 } } },
      { "$sort": { "customer_info_count": -1 } },
      { "$limit": limit }
    ]
    lookup_collection(
      agg_stages=agg_stages, 
      target_col=self.estate_info_collection.name,
      local_field="_id",
      as_field="estate_info",
    )
    agg_stages.append({
      "$replaceRoot": {
        "newRoot": {
          "$mergeObjects": [
            "$estate_info",
            { "customer_info_count": "$customer_info_count" },
          ]
        } 
      }
    })
    result = list(self.customer_info_collection.aggregate(agg_stages))
    return result
  