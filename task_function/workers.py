import pymongo
import os
import pytz
import traceback
from datetime import datetime
from constants import TaskStates, TaskTypes, enum_set
from config import Config
from task_function.estate_customer_info_import import process_customer_xlsx

def process_task(task_id, max_retrial=5, collection_name="bgtasks"):
  mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)    
  db = mongo_client.get_database()
  task_col = db.get_collection(collection_name)
  result = None
  for i in range(max_retrial):
    task = task_col.find_one_and_update(
      { "_id": task_id },
      { 
        "$set": {
          "state": TaskStates.running,
          "trial": i + 1,
          "run_at": datetime.now(pytz.UTC),
          "system_pid": os.getpid(),
        }
      }
    )
    try:
      if task["task_type"] == TaskTypes.import_customer_xlsx:
        params = task["params"]
        file_path = params["fs_path"]
        estate_info_id = params["estate_info_id"]
        result = process_customer_xlsx(file_path, estate_info_id, mongo_client=mongo_client)
        break
      else:
        raise ValueError("task_type should be one of %s" % enum_set(TaskTypes))
    except Exception as e:
      task_col.update_one(
        { "_id": task_id },
        { 
          "$set": {
            "state": TaskStates.failed,
            "message": traceback.format_exc(),
          }
        }
      )
      return
    
  # Mark task as completed
  task_col.update_one(
    { "_id": task_id },
    { 
      "$set": {
        "state": TaskStates.success,
        "message": result,
        "finished_at": datetime.now(pytz.UTC),
      }
    }
  )
