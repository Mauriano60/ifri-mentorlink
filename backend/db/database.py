import os
from contextlib import contextmanager

import pymysql
from dotenv import load_dotenv

load_dotenv()


def db_config():
    config = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "ifri_mentorlink"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }
    # Ajout SSL si certificat présent (pour Aiven)
    ca_path = os.path.join(os.path.dirname(__file__), '..', '..', 'aiven-ca.pem')
    if os.path.exists(ca_path):
        config["ssl"] = {"ca": ca_path}
    return config

@contextmanager
def get_db():
    connection = pymysql.connect(**db_config())
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def fetch_one(sql, params=None):
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()


def fetch_all(sql, params=None):
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()


def execute(sql, params=None):
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.lastrowid

