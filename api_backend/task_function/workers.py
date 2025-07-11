import sys
import pymongo
import os
import pytz
import traceback
from api_backend.task_function.customer_blacklist_import import discard_customer_blacklist_xlsx_import_draft, import_customer_blacklist_draft_to_live, import_customer_blacklist_xlsx_to_draft
from api_backend.task_function.estate_customer_info_export import export_customer_xlsx
from api_backend.task_function.estate_customer_info_import import (
  discard_customer_xlsx_import_draft,
  import_customer_draft_to_live,
  import_customer_xlsx_to_draft,
)
from constants import TaskStates, TaskTypes, enum_set
from config import Config
from datetime import datetime

def process_task(task_id, max_retrial=5, collection_name="bgtasks"):
  mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)    
  task_col = mongo_client.get_database().get_collection(collection_name)
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
      if task["task_type"] == TaskTypes.import_customer_blacklist_xlsx_to_draft:
        result = import_customer_blacklist_xlsx_to_draft(task, mongo_client)
        break
      elif task["task_type"] == TaskTypes.import_customer_blacklist_draft_to_live:
        result = import_customer_blacklist_draft_to_live(task, collection_name, mongo_client)
        break
      elif task["task_type"] == TaskTypes.discard_customer_blacklist_xlsx_import_draft:
        result = discard_customer_blacklist_xlsx_import_draft(task, mongo_client)
        break
      elif task["task_type"] == TaskTypes.import_customer_xlsx_to_draft:
        result = import_customer_xlsx_to_draft(task, mongo_client)
        break
      elif task["task_type"] == TaskTypes.import_customer_draft_to_live:
        result = import_customer_draft_to_live(task, collection_name, mongo_client)
        break
      elif task["task_type"] == TaskTypes.discard_customer_xlsx_import_draft:
        result = discard_customer_xlsx_import_draft(task, mongo_client)
        break
      elif task["task_type"] == TaskTypes.export_customer_xlsx:
        result = export_customer_xlsx(task, mongo_client)
        break
      else:
        raise ValueError("task_type should be one of %s" % enum_set(TaskTypes))
    except Exception as e:
      err_msg = traceback.format_exc()
      print(err_msg, file=sys.stderr)
      task_col.update_one(
        { "_id": task_id },
        { 
          "$set": {
            "state": TaskStates.failed,
            "result": { "message": str(e), "traceback": err_msg }
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
        "result": result,
        "finished_at": datetime.now(pytz.UTC),
      }
    }
  )
