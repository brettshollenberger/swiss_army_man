import os
import psycopg2
from contextlib import contextmanager
from .. import project_root, db_config
class DatabaseManager():
    @contextmanager
    @staticmethod
    def with_cursor(host=None, dbname=None, port=None):
        if os.path.exists(project_root("db/config.yml")) and host is None:
            config = db_config()
            host = config["host"]
            dbname = config["database"]
            port = config["port"]

        conn = psycopg2.connect(
            dbname=dbname,
            host=host,
            port=port
        )
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        finally:
            cursor.close()
            conn.close()