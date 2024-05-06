import os
import psycopg2
import pandas as pd
from contextlib import contextmanager
from .. import project_root, db_config
class DatabaseManager():
    @staticmethod
    def prepare_connection(host=None, dbname=None, port=None):
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
        return conn

    @contextmanager
    @staticmethod
    def with_cursor(host=None, dbname=None, port=None):
        conn = DatabaseManager.prepare_connection(host=host, dbname=dbname, port=port)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    @contextmanager
    @staticmethod
    def with_conn(host=None, dbname=None, port=None):
        conn = DatabaseManager.prepare_connection(host=host, dbname=dbname, port=port)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
 
    @staticmethod
    def to_dataframe(query=None, host=None, dbname=None, port=None):
        with DatabaseManager.with_conn(host=host,dbname=dbname,port=port) as conn:
            return pd.read_sql_query(query, conn)
