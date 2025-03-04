import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'bddpnj.db')
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    STATIC_IMAGES_PNJ_DIR = os.path.join(STATIC_DIR, 'images', 'pnj')
    INDEX_DIR = os.path.join(BASE_DIR, 'indexdir')

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Limite des fichiers uploadés fixée à 10 Mo
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    SECRET_KEY = 'votre_clef_secrete'
