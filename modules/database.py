import sqlite3
from flask import g
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATABASE_PATH = os.path.join(BASE_DIR, 'bddpnj.db')

def get_db():
    if 'db' not in g:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db

def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()
