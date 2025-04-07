import multiprocessing
import pymongo
import pytz
import constants
import os
import bson
import werkzeug.exceptions
from config import Config
from PIL import Image
from datetime import datetime
from task_function.process_member_xlsx import process_task
from utils import get_file_sha1

class FileOpsService():
  def __init__(
      self,
      mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
    ):
    self.upload_folder = Config.FS_UPLOAD_FOLDER_NAME
    self.upload_path = os.path.join(Config.FS_UPLOAD_ROOT, self.upload_folder)
    self.url_pfx = Config.FS_RETURN_UPLOAD_URL_PFX
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.task_col = self.db.schedulertasks
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
  
  def upload_and_process_member_xlsx(self, uid, xlsx_file):
    if xlsx_file.filename == '':
      raise werkzeug.exceptions.BadRequest('no file found')
    if xlsx_file.mimetype not in constants.XLSX_MIME_TYPES:
      raise werkzeug.exceptions.BadRequest(
        'available mimetypes: %s' % (
          ', '.join(mimetype for mimetype in constants.XLSX_MIME_TYPES)
        )
      )
    file_dir_final = os.path.join(self.upload_path, str(uid))
    file_name = '%s' % (str(bson.ObjectId()))
    file_ext = constants.XLSX_MIME_TYPES[xlsx_file.mimetype]
    final_file_path = os.path.join(file_dir_final, '%s.%s' % (file_name, file_ext))
    xlsx_file.save(final_file_path)
    task_entry = {}
    task_id = bson.ObjectId()
    task_entry.update(
      _id = task_id,
      task_type = constants.TaskTypes.import_customer_xlsx,
      state = constants.TaskStates.pending,
      creator_id = uid,
      trial = 0,
      params = {
        "original_file_name": xlsx_file.filename,
        "file_hash": get_file_sha1(final_file_path),
        "fs_path": final_file_path,
      },
      messages = '',
      system_pid = 0,
      created_at = datetime.now(pytz.UTC),
      run_at = None,
      finished_at = None,
    )
    self.task_col.insert_one(task_entry)

    # process task
    process = multiprocessing.Process(target=process_task, args=(task_id, ))
    process.start()
    return task_entry

  def upload_image(self, uid, image_file, preferred_max_size=2048):
    if image_file.filename == '':
      raise werkzeug.exceptions.BadRequest('no file found')
    if image_file.mimetype not in constants.ALLOWED_IMAGE_MIME_TYPES:
      raise werkzeug.exceptions.BadRequest(
        'available mimetypes: %s' % (
          ', '.join(mimetype for mimetype in constants.ALLOWED_IMAGE_MIME_TYPES)
        )
      )
    file_ext = constants.ALLOWED_IMAGE_MIME_TYPES[image_file.mimetype]
    file_dir_final = os.path.join(self.upload_path, str(uid))
    if not os.path.isdir(file_dir_final):
      os.makedirs(file_dir_final, exist_ok=True)

    file_name = '%s' % (str(bson.ObjectId()))
    tmp_image_path = os.path.join(file_dir_final, '.%s.%s' % (file_name, file_ext))
    image_file.save(tmp_image_path)
    try:
      final_image_path, new_width, new_height = self.compact_image(
        tmp_image_path,
        file_dir_final,
        file_name,
        preferred_max_size
      )
      os.remove(tmp_image_path)
      return os.path.join(self.url_pfx, str(uid), os.path.basename(final_image_path)), new_width, new_height
    except:
      raise werkzeug.exceptions.InternalServerError('processing image failed')
    
  def compact_image(self, old_path, file_dir_final, new_file_name, preferred_max_size=2048):
    with Image.open(old_path) as img:
      width, height = img.size
      if max(width, height) > preferred_max_size:
        if width > height:
          new_width = preferred_max_size
          new_height = int(height * (preferred_max_size / width)) or 1
        else:
          new_height = preferred_max_size
          new_width = int(width * (preferred_max_size / height)) or 1
      else:
        new_width, new_height = width, height
      resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
      final_image_name = new_file_name + '.webp'
      final_image_path = os.path.join(file_dir_final, final_image_name)
      resized_img.save(final_image_path, "WEBP")
      return final_image_path, new_width, new_height
    
