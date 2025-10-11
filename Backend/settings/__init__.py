import os, sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))

from dotenv import load_dotenv
from utils.log import logger 
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
logger.info("Loaded environment variables from .env file")

DEBUG = os.getenv('DEBUG', False)
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = os.getenv('FLASK_PORT', 8080)

API_KEY = os.getenv('API_KEY', None)
BASE_URL = os.getenv('BASE_URL', None)

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', None)
DEFAULT_TONGYI_MODEL = os.getenv('DEFAULT_TONGYI_MODEL', None)
DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_MAX_RETRIES = 3

ENABLE_LLM_FILTERING=True