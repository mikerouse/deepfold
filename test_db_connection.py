import os
import MySQLdb
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"Loaded DATABASE_URL: {DATABASE_URL}")

url = urlparse(DATABASE_URL)
try:
    conn = MySQLdb.connect(
        host=url.hostname,
        user=url.username,
        passwd=url.password,
        db=url.path[1:],  # Remove leading '/'
        port=url.port
    )
    print("Connection successful using DATABASE_URL " + DATABASE_URL)
    conn.close()
except Exception as e:
    print(f"Connection failed using DATABASE_URL " + DATABASE_URL)
    print(e)