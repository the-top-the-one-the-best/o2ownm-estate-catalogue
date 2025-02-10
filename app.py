import argparse
import logging

from api_backend import make_app
from config import Config


def _main():
  try:
    parsed_args = _parse_args()
    logger = logging.getLogger()
    logger.setLevel(logging.getLevelName(parsed_args.logging_level.upper()))
    app, with_app_context_wraps = make_app(Config, False)
    app.run(
      host=app.config["APP_HOST"], port=app.config["APP_PORT"], debug=True, use_reloader=True
    )
  except KeyboardInterrupt:
    pass
  except Exception as e:
    logging.exception(e)
    raise


def _parse_args(args=None):
  parser = argparse.ArgumentParser()
  parser.add_argument("-ll", "--logging-level", type=str, default="info", help="logging level")
  parsed_args = parser.parse_args(args)
  return parsed_args


if __name__ == "__main__":
  _main()

