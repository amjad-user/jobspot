"""Settings for JobSpot.

Settings are read from the ".env" file in the project folder.
If a setting is missing, a safe default value is used, so the app
also works without any ".env" file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# The project folder (one level above this "backend" folder)
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Read the .env file (if it exists) into the environment variables
load_dotenv(PROJECT_DIR / ".env")

# Port number for the local web page
PORT = int(os.getenv("JOBSPOT_PORT", "8000"))

# Where the saved jobs database file lives
db_path_text = os.getenv("JOBSPOT_DB_PATH", "data/jobspot.db")
DB_PATH = Path(db_path_text)
if not DB_PATH.is_absolute():
    DB_PATH = PROJECT_DIR / DB_PATH

# Key for the Bundesagentur job search service (public key, not a secret)
JOBSUCHE_API_KEY = os.getenv("JOBSUCHE_API_KEY", "jobboerse-jobsuche")

# Folder with the web page files (HTML, CSS, JavaScript)
FRONTEND_DIR = PROJECT_DIR / "frontend"
