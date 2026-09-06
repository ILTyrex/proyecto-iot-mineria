import os
import psycopg
from dotenv import load_dotenv

load_dotenv(".env")
url = os.getenv("TIMESCALE_SERVICE_URL")
if url:
    conn_str = url
else:
    conn_str = (
        f"host={os.getenv('DB_HOST')} port={os.getenv('DB_PORT')} "
        f"user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} "
        f"dbname={os.getenv('DB_NAME')} sslmode={os.getenv('DB_SSLMODE')}"
    )

c = psycopg.connect(conn_str)
print("Conexion OK")
c.close()
