import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load variables from .env file (safe no-op if file doesn't exist)
load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise EnvironmentError(
        "MONGO_URI is not set. Add it to your .env file or set it as an environment variable."
    )

client = MongoClient(MONGO_URI)

db = client["job_scraper_db"]

jobs_collection = db["jobs"]