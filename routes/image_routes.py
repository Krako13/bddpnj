from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from modules.database import get_db
from PIL import Image
import os

image_bp = Blueprint('image_bp', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def is_image_valid(file_stream):
    try:
        img = Image.open(file_stream)
        img.verify()
        file_stream.seek(0)
        return True
    except Exception as e:
        print(f"Image invalide: {e}")
        return False

@image_bp.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        id = request.form.get('id')
        file = request.files.get('image')
        if file and id:
            filename = secure_filename(file.filename)
            if allowed_file(filename) and is_image_valid(file.stream):
                id = int(id)
                os.makedirs(current_app.config['STATIC_IMAGES_PNJ_DIR'], exist_ok=True)
                extension = filename.rsplit('.', 1)[1].lower()
                saved_filename = f'{id}.jpg'
                file_path = os.path.join(current_app.config['STATIC_IMAGES_PNJ_DIR'], saved_filename)
                file.save(file_path)
                conn = get_db()
                conn.execute('UPDATE pnj SET Image = ? WHERE Id = ?', (saved_filename, id))
                conn.commit()
                print(f"Image uploadée avec succès pour l'ID {id}.")
                return jsonify({"success": True, "message": "Image uploadée avec succès."})
            else:
                return jsonify({"success": False, "message": "Type de fichier non autorisé ou fichier invalide."})
        return jsonify({"success": False, "message": "Aucun fichier ou ID fourni."})
    except Exception as e:
        print(f"Une erreur lors de l'upload de l'image: {e}")
        return jsonify({"error": str(e)})

@image_bp.route('/static/images/pnj/<filename>')
def serve_image(filename):
    response = send_from_directory(current_app.config['STATIC_IMAGES_PNJ_DIR'], filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
