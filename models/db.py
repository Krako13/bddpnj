# models/db.py
import sqlite3
from flask import g
import os

# Définir le chemin absolu vers la base de données.
# Le chemin est calculé en remontant d'un niveau depuis le dossier "models"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATABASE_PATH = os.path.join(BASE_DIR, 'bddpnj.db')

def get_db():
    """
    Retourne une connexion à la base de données SQLite.
    La connexion est stockée dans l'objet contextuel "g" afin d'être réutilisée.
    """
    if 'db' not in g:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db

def close_connection(exception):
    """
    Ferme la connexion à la base de données si elle existe.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()
