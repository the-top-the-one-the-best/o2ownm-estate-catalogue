import smtplib
import sys
import traceback
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bson import ObjectId
from flask import render_template
from config import Config

class EmailService:
  def __init__(
    self,
    sender=Config.SYSTEM_EMAIL_USER,
    sender_pwd=Config.SYSTEM_EMAIL_APP_PASSWORD,
    smtp_server=Config.SYSTEM_SMTP_SERVER,
    smtp_port=Config.SYSTEM_SMTP_PORT,
  ):
    self.sender = sender
    self.sender_pwd = sender_pwd
    self.smtp_server = smtp_server
    self.smtp_port = smtp_port
    self.chpwd_frontend_url = Config.CHANGE_PWD_FRONTEND_URL

  def send_email_notify(
      self,
      recipient,
      subject,
      content,
      content_type="plain",
      raise_error=False,
    ):
    msg = MIMEMultipart()
    msg["From"] = self.sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(content, content_type))
    try:
      server = smtplib.SMTP(self.smtp_server, self.smtp_port)
      server.starttls()
      server.login(self.sender, self.sender_pwd)
      server.sendmail(self.sender, recipient, msg.as_string())
      server.quit()
    except Exception as e:
      print(traceback.format_exc(e), file=sys.stderr)
      if raise_error:
        raise e

    return
  
  def generate_password_reset_mail_html(
    self,
    event_id: ObjectId,
    salt: str,
  ):
    qs = urllib.parse.urlencode({'event_id': str(event_id)})
    reset_url = self.chpwd_frontend_url + '?' + qs
    return render_template("reset_password.html", reset_url=reset_url, salt=salt)
