import multiprocessing
import pymongo
import pytz
from api_backend.services.estate_info import EstateInfoService
from api_backend.task_function.workers import process_task
import constants
import os
import bson
import werkzeug.exceptions
from config import Config
from datetime import datetime

class BackgroundTaskService():
  def __init__(
      self,
      mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
    ):
    self.upload_folder = Config.FS_UPLOAD_FOLDER_NAME
    self.upload_path = os.path.join(Config.FS_UPLOAD_ROOT, self.upload_folder)
    self.url_pfx = Config.FS_RETURN_UPLOAD_URL_PFX
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.bgtasks
    self.estate_service = EstateInfoService()
    os.makedirs(self.upload_path, exist_ok=True)
    return
  
  def remove_from_fs(self, resource_url: str):
    if not resource_url:
      return
    if self.upload_folder in resource_url:
      rel_path = resource_url.split(self.upload_folder)[-1]
      while rel_path.startswith('/'):
        rel_path = rel_path[1:]
      abs_path = os.path.join(self.upload_path, rel_path)
      try:
        os.remove(abs_path)
      except:
        return
  
  def upload_and_process_estate_customer_info_xlsx(
    self,
    user_id,
    estate_info_id,
    xlsx_file,
    auto_create_customer_tags=False,
    overwrite_existing_user_by_phone=False,
    timezone_offset=+8,
  ):
    if xlsx_file.filename == '':
      raise werkzeug.exceptions.BadRequest('no file found')
    if xlsx_file.mimetype not in constants.XLSX_MIME_TYPES:
      raise werkzeug.exceptions.BadRequest(
        'available mimetypes: %s' % (
          ', '.join(mimetype for mimetype in constants.XLSX_MIME_TYPES)
        )
      )
    self.estate_service.find_by_id(estate_info_id)
    file_dir_final = os.path.join(self.upload_path, str(user_id))
    os.makedirs(file_dir_final, exist_ok=True)
    file_name = '%s' % (str(bson.ObjectId()))
    file_ext = constants.XLSX_MIME_TYPES[xlsx_file.mimetype]
    final_file_path = os.path.join(file_dir_final, '%s.%s' % (file_name, file_ext))
    xlsx_file.save(final_file_path)
    task_entry = {}
    task_id = bson.ObjectId()
    task_entry.update(
      _id = task_id,
      task_type = constants.TaskTypes.import_customer_xlsx_to_draft,
      state = constants.TaskStates.pending,
      creator_id = user_id,
      trial = 0,
      params = {
        "original_file_name": xlsx_file.filename,
        "fs_path": final_file_path,
        "estate_info_id": estate_info_id,
        "auto_create_customer_tags": auto_create_customer_tags,
        "overwrite_existing_user_by_phone": overwrite_existing_user_by_phone,
        "timezone_offset": timezone_offset,
      },
      messages = '',
      system_pid = 0,
      created_at = datetime.now(pytz.UTC),
      run_at = None,
      finished_at = None,
    )
    self.collection.insert_one(task_entry)

    # process task
    process = multiprocessing.Process(target=process_task, args=(task_id, ))
    process.start()
    return task_entry

  def get_task_by_id(self, _id):
    target = self.collection.find_one({ "_id": _id })
    if not target:
      raise werkzeug.exceptions.NotFound()
    return target
