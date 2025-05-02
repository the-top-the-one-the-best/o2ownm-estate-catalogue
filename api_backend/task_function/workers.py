import sys
import pymongo
import os
import pytz
import traceback
from datetime import datetime
from api_backend.task_function.estate_customer_info_import import process_customer_xlsx_into_draft
from constants import TaskStates, TaskTypes, enum_set
from config import Config

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
      if task["task_type"] == TaskTypes.import_customer_xlsx_to_draft:
        result = process_customer_xlsx_into_draft(task)
        break
      else:
        raise ValueError("task_type should be one of %s" % enum_set(TaskTypes))
    except Exception as e:
      err_msg = traceback.format_exc()
      print(err_msg, file=sys.stderr)
      task_col.update_one(
        { "_id": task_id },
        { "$set": { "state": TaskStates.failed, "message": err_msg } }
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
