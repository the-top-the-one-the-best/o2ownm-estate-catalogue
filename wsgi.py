from config import Config
from api_backend import make_app

app = make_app(Config, False).app
