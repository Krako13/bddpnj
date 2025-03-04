from flask import Flask, render_template, request, jsonify, send_from_directory, g
import os, math
from config import Config
from routes.pnj_routes import pnj_bp
from routes.image_routes import image_bp
from utils.security import set_security_headers
from modules.database import get_db, close_connection
# Nous n'initialisons plus globalement les données PNJ afin d'éviter les erreurs de contexte
# from modules.pnj import get_pnj_data
from modules.search import create_whoosh_index
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__, template_folder=Config.TEMPLATE_DIR, static_folder=Config.STATIC_DIR)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Enregistrement des Blueprints
app.register_blueprint(pnj_bp)
app.register_blueprint(image_bp)

# Ajout des en-têtes de sécurité
app.after_request(set_security_headers)

@app.teardown_appcontext
def teardown_db(exception):
    close_connection(exception)

# Route pour la page d'accueil
@app.route('/')
def home():
    return render_template('home.html')

# Route pour la page PNJ Laelith (définie ici pour conserver l'endpoint d'origine)
@app.route('/pnjlaelith', methods=['GET', 'POST'])
def pnjlaelith():
    try:
        conn = get_db()
        lieu = request.args.get('lieu', '')
        search = request.args.get('search', '').lower()
        page = int(request.args.get('page', 1))
        per_page = 9

        query = 'SELECT * FROM laelith_pnj WHERE 1=1'
        params = []
        if lieu:
            query += ' AND lieu = ?'
            params.append(lieu)
        if search:
            query += ' AND LOWER(nom) LIKE ?'
            params.append(f'%{search}%')

        total_pnjs = conn.execute(f'SELECT COUNT(*) FROM ({query})', params).fetchone()[0]
        total_pages = max(1, math.ceil(total_pnjs / per_page))
        offset = (page - 1) * per_page
        query += ' LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        pnjs = conn.execute(query, params).fetchall()

        # Récupérer la liste des lieux distincts pour le filtre
        lieux = conn.execute('SELECT DISTINCT lieu FROM laelith_pnj WHERE lieu IS NOT NULL AND lieu != "" ORDER BY lieu').fetchall()
        lieux_list = [row['lieu'] for row in lieux]

        return render_template('pnjlaelith.html', 
                               pnjs=pnjs, 
                               lieux=lieux_list, 
                               lieu_selected=lieu, 
                               search_query=search, 
                               page=page, 
                               total_pages=total_pages)
    except Exception as e:
        print(f"Erreur lors du chargement des PNJ de Laelith : {e}")
        return "Une erreur s'est produite lors du chargement des PNJ de Laelith."

# Les routes suivantes sont restées inchangées
@app.route('/pnj', methods=['GET', 'POST'])
def pnj_table():
    try:
        category = request.args.get('category', '')
        keyword = request.args.get('keyword', '').lower()
        sexe = request.args.get('sexe', '')
        race = request.args.get('race', '')
        action = request.args.get('action', 'filter')
        page = int(request.args.get('page', 1))
        per_page = 9

        print(f"Received request with keyword: {keyword}, category: {category}, sexe: {sexe}, race: {race}, action: {action}")

        # Appeler get_pnj_data() à la demande pour éviter l'accès hors contexte
        from modules.pnj import get_pnj_data
        data = get_pnj_data()
        filtered_data = data.copy()

        if sexe:
            filtered_data = filtered_data[filtered_data['Sexe'] == sexe]
        if race:
            filtered_data = filtered_data[filtered_data['Race'] == race]
        if category:
            filtered_data = filtered_data[filtered_data['Catégorie'] == category]

        if action == 'random':
            if not filtered_data.empty:
                filtered_data = filtered_data.sample(n=1)
        elif keyword:
            print(f"Searching for: {keyword}")
            try:
                from whoosh import index as whoosh_index
                ix = whoosh_index.open_dir(Config.INDEX_DIR)
                with ix.searcher() as searcher:
                    results = create_whoosh_index()  # TODO: intégrer la recherche avancée si besoin
            except Exception as e:
                print(f"Erreur lors de la recherche Whoosh: {e}")
        total_pages = max(1, math.ceil(len(filtered_data) / per_page))
        start = (page - 1) * per_page
        end = start + per_page
        pnjs_on_page = filtered_data.iloc[start:end]

        return render_template('pnj.html',
                               filtered_data=pnjs_on_page,
                               category_description="",
                               keyword=keyword,
                               category=category,
                               sexe=sexe,
                               race=race,
                               page=page,
                               total_pages=total_pages)
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return f"Une erreur s'est produite : {e}"

@app.route('/get_data', methods=['POST'])
def get_data():
    try:
        category = request.form.get('category', '')
        keyword = request.form.get('keyword', '').lower()
        sexe = request.form.get('sexe', '')
        race = request.form.get('race', '')
        action = request.form.get('action', 'filter')
        page = int(request.form.get('page', 1))
        per_page = 9

        from modules.pnj import get_pnj_data
        data = get_pnj_data()
        filtered_data = data.copy()
        if sexe:
            filtered_data = filtered_data[filtered_data['Sexe'] == sexe]
        if race:
            filtered_data = filtered_data[filtered_data['Race'] == race]
        if category:
            filtered_data = filtered_data[filtered_data['Catégorie'] == category]
        if action == 'random':
            if not filtered_data.empty:
                filtered_data = filtered_data.sample(n=1)
        elif keyword:
            print(f"Searching for: {keyword}")
            try:
                from whoosh import index as whoosh_index
                ix = whoosh_index.open_dir(Config.INDEX_DIR)
                with ix.searcher() as searcher:
                    results = create_whoosh_index()  # Ou utiliser la recherche avancée
                    # Pour l'instant, nous ne filtrons pas par recherche avancée
            except Exception as e:
                print(f"Erreur lors de la recherche Whoosh: {e}")
                if not os.path.exists(Config.INDEX_DIR):
                    create_whoosh_index()
        total_pages = max(1, math.ceil(len(filtered_data) / per_page))
        start = (page - 1) * per_page
        end = start + per_page
        pnjs_on_page = filtered_data.iloc[start:end]

        return jsonify({
            "pnjs": pnjs_on_page.to_dict(orient='records'),
            "total_pages": total_pages,
            "current_page": page
        })
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return jsonify({"error": str(e)})

@app.route('/get_races', methods=['POST'])
def get_races():
    try:
        from modules.pnj import get_pnj_data
        data = get_pnj_data()
        races = data['Race'].unique().tolist()
        return jsonify(races)
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return jsonify({"error": str(e)})

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        id = request.form.get('id')
        file = request.files.get('image')
        if file and id:
            filename = secure_filename(file.filename)
            if allowed_file(filename) and __import__('PIL').Image.open(file.stream).verify() is None:
                # Vérifier la validité de l'image
                if __import__('PIL').Image.open(file.stream) is None:
                    pass  # Ceci ne doit normalement pas arriver
            # Nous utilisons désormais la fonction is_image_valid dans routes/image_routes.py
            # pour éviter d'écrire trop de logique ici.
            # Les instructions de sécurité sont gérées dans le Blueprint image_routes.
            # Ce bloc n'est ici qu'une redondance de backup (mais mieux vaut ne pas l'utiliser).
            # Pour être cohérent, nous allons laisser la logique d'upload dans le Blueprint image_routes.
            # Ainsi, ici nous renvoyons une erreur pour éviter les incohérences.
            return jsonify({"success": False, "message": "Utilisez le point d'upload défini dans le Blueprint image_routes."})
        return jsonify({"success": False, "message": "Aucun fichier ou ID fourni."})
    except Exception as e:
        print(f"Une erreur lors de l'upload de l'image : {e}")
        return jsonify({"error": str(e)})

@app.route('/static/images/pnj/<filename>')
def serve_image(filename):
    response = send_from_directory(Config.STATIC_IMAGES_PNJ_DIR, filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    if not os.path.exists(Config.INDEX_DIR):
        print("L'index n'existe pas, création en cours...")
        create_whoosh_index()
    else:
        print("Recréation de l'index avec l'analyseur amélioré...")
        create_whoosh_index()
    app.run(debug=True)
