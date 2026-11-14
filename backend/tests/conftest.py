import os
import tempfile

os.environ["NARADIG_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["NARADIG_SECRET"] = "test-secret"
os.environ["NARADIG_ENV"] = "development"
os.environ["NARADIG_RSS_FEEDS"] = ""
os.environ["NARADIG_FACTCHECK_FEEDS"] = ""
os.environ["NARADIG_BACKUP_DIR"] = os.path.join(tempfile.mkdtemp(), "backups")
os.environ["REDIS_URL"] = ""