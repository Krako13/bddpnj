from flask import Flask, render_template, request, jsonify, send_from_directory, g
import pandas as pd
import nltk
import spacy
from googletrans import Translator
from whoosh.fields import Schema, ID, TEXT
from whoosh.analysis import StemmingAnalyzer, LanguageAnalyzer
from whoosh import index as whoosh_index
from whoosh.qparser import MultifieldParser
from whoosh.qparser import QueryParser
import os
import math
import sqlite3
import numpy as np
import re
import shutil

# Télécharger les ressources nécessaires pour NLTK
try:
    nltk.download('wordnet')
    nltk.download('omw-1.4')  # Ressources multilingues pour WordNet
    print("NLTK resources downloaded successfully.")
except Exception as e:
    print(f"Error downloading NLTK resources: {e}")

# Charger le modèle spaCy pour le français
try:
    nlp = spacy.load('fr_core_news_sm')
    print("spaCy model loaded successfully.")
except Exception as e:
    print(f"Error loading spaCy model: {e}")

app = Flask(__name__)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('bddpnj.db')
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_pnj_data():
    with app.app_context():
        conn = get_db()
        query = "SELECT * FROM pnj"
        df = pd.read_sql_query(query, conn)
        return df

# Charger les données depuis la base de données SQLite
pnj_data = get_pnj_data()

# Descriptions des catégories en français
category_descriptions = {
    "Taverne": "PNJ que l'on peut rencontrer dans des tavernes, où les aventuriers se retrouvent pour boire, échanger des histoires et parfois trouver du travail. Les tavernes sont souvent des lieux animés où les informations circulent librement.",
    "Lieu Malfamé": "PNJ que l'on peut rencontrer dans des lieux dangereux ou illégaux, souvent impliqués dans des activités criminelles. Ces endroits sont fréquentés par des individus louches et des hors-la-loi.",
    "Forêt/Nature": "PNJ que l'on peut rencontrer dans des environnements naturels, comme les forêts ou les montagnes. Ces personnages sont souvent des chasseurs, des ermites ou des créatures sauvages.",
    "Marché": "PNJ que l'on peut rencontrer dans des lieux publics comme les marchés ou les places de village. Ces endroits sont propices aux rencontres et aux échanges commerciaux.",
    "Bibliothèque Ancienne": "PNJ que l'on peut rencontrer dans des lieux de savoir ancien comme les bibliothèques ou les archives. Ces personnages sont souvent des érudits ou des gardiens de connaissances oubliées.",
    "Château/Palais": "PNJ que l'on peut rencontrer dans des lieux de pouvoir comme les châteaux ou les palais. Ces personnages sont souvent des nobles, des conseillers ou des gardes royaux.",
    "Guilde/Atelier": "PNJ que l'on peut rencontrer dans des lieux de travail comme les guildes ou les ateliers d'artisans. Ces personnages sont souvent des artisans, des marchands ou des membres de guildes.",
    "Militaire": "PNJ que l'on peut rencontrer dans des contextes militaires comme les camps d'entraînement ou les forteresses. Ces personnages sont souvent des soldats, des officiers ou des stratèges.",
    "Port/Quai": "PNJ que l'on peut rencontrer dans des lieux maritimes comme les ports ou les quais. Ces personnages sont souvent des marins, des pêcheurs ou des marchands.",
    "Temple/Église": "PNJ que l'on peut rencontrer dans des lieux sacrés comme les temples ou les églises. Ces personnages sont souvent des prêtres, des moines ou des fidèles.",
    "Rue/Place Publique": "PNJ que l'on peut rencontrer dans les rues ou les places publiques des villes et villages. Ces endroits sont animés et propices aux rencontres fortuites."
}

# Créer le schéma pour Whoosh
# Essayer d'abord avec un analyseur de langue française
try:
    analyzer = LanguageAnalyzer('fr')
    print("Using LanguageAnalyzer for French")
except Exception as e:
    print(f"Error with LanguageAnalyzer: {e}")
    # Fallback sur StemmingAnalyzer si LanguageAnalyzer échoue
    analyzer = StemmingAnalyzer(lang='french')
    print("Using StemmingAnalyzer for French")

schema = Schema(
    id=ID(unique=True, stored=True),
    nom=TEXT(stored=True, analyzer=analyzer),
    description=TEXT(stored=True, analyzer=analyzer),
    categorie=TEXT(stored=True, analyzer=analyzer),
    sexe=TEXT(stored=True),
    race=TEXT(stored=True)
)

# Afficher les composants du schéma pour vérification
print(f"Schema components: {schema.names()}")

# Créer l'index Whoosh
def create_whoosh_index():
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")
    ix = whoosh_index.create_in("indexdir", schema)
    writer = ix.writer()
    
    print(f"Nombre de PNJ à indexer: {len(pnj_data)}")
    for _, row in pnj_data.iterrows():
        try:
            writer.add_document(
                id=str(row['Id']),
                nom=row['Nom'],
                description=row['Description'],
                categorie=row['Catégorie'],
                sexe=row['Sexe'],
                race=row['Race']
            )
            print(f"Indexed: {row['Nom']}")
        except Exception as e:
            print(f"Erreur d'indexation pour {row['Nom']}: {e}")
    
    writer.commit()
    print("Index Whoosh créé avec succès.")
    
    # Vérification des termes indexés
    with ix.searcher() as searcher:
        try:
            # Afficher quelques termes du lexique pour vérifier
            lexicon = list(searcher.lexicon("description"))[:20]
            print(f"Exemples de termes indexés: {lexicon}")
        except Exception as e:
            print(f"Erreur lors de la vérification du lexique: {e}")

# Route principale
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        category = request.args.get('category', '')
        keyword = request.args.get('keyword', '').lower()
        sexe = request.args.get('sexe', '')
        race = request.args.get('race', '')
        action = request.args.get('action', 'filter')
        page = int(request.args.get('page', 1))
        per_page = 9

        print(f"Received request with keyword: {keyword}, category: {category}, sexe: {sexe}, race: {race}, action: {action}")

        # Filtrer par sexe et race si sélectionnés
        filtered_data = pnj_data.copy()
        if sexe:
            filtered_data = filtered_data[filtered_data['Sexe'] == sexe]
        if race:
            filtered_data = filtered_data[filtered_data['Race'] == race]
        print(f"Filtered data after sexe and race filter: {filtered_data}")

        if action == 'random':
            filtered_data = filtered_data.sample(n=1)
            print(f"Filtered data after random selection: {filtered_data}")
        elif keyword:
            print(f"Searching for: {keyword}")  # Afficher le mot-clé de recherche
            try:
                # Ouvrir l'index Whoosh
                ix = whoosh_index.open_dir("indexdir")
                with ix.searcher() as searcher:
                    # Champs à rechercher
                    fields = ['nom', 'description', 'categorie']
                    parser = MultifieldParser(fields, schema=ix.schema)
                    
                    try:
                        query = parser.parse(keyword)
                        print(f"Query: {query}")
                        results = searcher.search(query, limit=None)
                        
                        # Si aucun résultat, essayer une recherche plus flexible
                        if len(results) == 0:
                            # Essayer une recherche OR sur tous les termes
                            keyword_with_or = " OR ".join(keyword.split())
                            query = parser.parse(keyword_with_or)
                            print(f"Trying with OR query: {query}")
                            results = searcher.search(query, limit=None)
                            
                            # Si toujours aucun résultat, essayer une recherche plus flexible
                            if len(results) == 0:
                                # Essayer une recherche avec caractères jokers
                                keyword_with_wildcard = f"*{keyword}*"
                                query = parser.parse(keyword_with_wildcard)
                                print(f"Trying with wildcard query: {query}")
                                results = searcher.search(query, limit=None)
                        
                        ids = [int(hit['id']) for hit in results]
                    except Exception as e:
                        print(f"Erreur de requête: {e}")
                        ids = []
                        
                    print(f"Search results: {ids}")  # Afficher les résultats de recherche

                    # Filtrer les données originales
                    filtered_data = filtered_data[filtered_data['Id'].isin(ids)]
                    print(f"Filtered data after search: {filtered_data}")
            except Exception as e:
                print(f"Erreur lors de la recherche Whoosh: {e}")
                # Si l'index n'existe pas, le créer
                if not os.path.exists("indexdir"):
                    print("L'index n'existe pas, création en cours...")
                    create_whoosh_index()
        else:
            filtered_data = filtered_data
            print(f"No keyword provided, using unfiltered data: {filtered_data}")

        # Filtrer par catégorie si sélectionnée
        if category:
            filtered_data = filtered_data[filtered_data['Catégorie'] == category]
            print(f"Filtered data after category filter: {filtered_data}")

        # Calculer le nombre total de pages
        total_pages = max(1, math.ceil(len(filtered_data) / per_page))
        print(f"Total pages: {total_pages}")

        # Obtenir les PNJ pour la page actuelle
        start = (page - 1) * per_page
        end = start + per_page
        pnjs_on_page = filtered_data.iloc[start:end]
        print(f"PNJs on current page: {pnjs_on_page}")

        return render_template('index.html',
                               filtered_data=pnjs_on_page,
                               category_description=category_descriptions.get(category, ""),
                               keyword=keyword,
                               category=category,
                               sexe=sexe,
                               race=race,
                               page=page,
                               total_pages=total_pages)
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return f"Une erreur s'est produite : {e}"

# Route pour récupérer les données via POST (si nécessaire)
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

        print(f"Received request with keyword: {keyword}, category: {category}, sexe: {sexe}, race: {race}, action: {action}")

        # Filtrer par sexe et race si sélectionnés
        filtered_data = pnj_data.copy()
        if sexe:
            filtered_data = filtered_data[filtered_data['Sexe'] == sexe]
        if race:
            filtered_data = filtered_data[filtered_data['Race'] == race]
        print(f"Filtered data after sexe and race filter: {filtered_data}")

        if action == 'random':
            filtered_data = filtered_data.sample(n=1)
            print(f"Filtered data after random selection: {filtered_data}")
        elif keyword:
            print(f"Searching for: {keyword}")  # Afficher le mot-clé de recherche
            try:
                # Ouvrir l'index Whoosh
                ix = whoosh_index.open_dir("indexdir")
                with ix.searcher() as searcher:
                    # Champs à rechercher
                    fields = ['nom', 'description', 'categorie']
                    parser = MultifieldParser(fields, schema=ix.schema)
                    
                    try:
                        query = parser.parse(keyword)
                        print(f"Query: {query}")
                        results = searcher.search(query, limit=None)
                        
                        # Si aucun résultat, essayer une recherche plus flexible
                        if len(results) == 0:
                            # Essayer une recherche OR sur tous les termes
                            keyword_with_or = " OR ".join(keyword.split())
                            query = parser.parse(keyword_with_or)
                            print(f"Trying with OR query: {query}")
                            results = searcher.search(query, limit=None)
                            
                            # Si toujours aucun résultat, essayer une recherche avec caractères jokers
                            if len(results) == 0:
                                # Essayer une recherche avec caractères jokers
                                keyword_with_wildcard = f"*{keyword}*"
                                query = parser.parse(keyword_with_wildcard)
                                print(f"Trying with wildcard query: {query}")
                                results = searcher.search(query, limit=None)
                        
                        ids = [int(hit['id']) for hit in results]
                    except Exception as e:
                        print(f"Erreur de requête: {e}")
                        ids = []
                        
                    print(f"Search results: {ids}")  # Afficher les résultats de recherche

                    # Filtrer les données originales
                    filtered_data = filtered_data[filtered_data['Id'].isin(ids)]
                    print(f"Filtered data after search: {filtered_data}")
            except Exception as e:
                print(f"Erreur lors de la recherche Whoosh: {e}")
                # Si l'index n'existe pas, le créer
                if not os.path.exists("indexdir"):
                    print("L'index n'existe pas, création en cours...")
                    create_whoosh_index()
        else:
            filtered_data = filtered_data
            print(f"No keyword provided, using unfiltered data: {filtered_data}")

        # Filtrer par catégorie si sélectionnée
        if category:
            filtered_data = filtered_data[filtered_data['Catégorie'] == category]
            print(f"Filtered data after category filter: {filtered_data}")

        # Calculer le nombre total de pages
        total_pages = max(1, math.ceil(len(filtered_data) / per_page))
        print(f"Total pages: {total_pages}")

        # Obtenir les PNJ pour la page actuelle
        start = (page - 1) * per_page
        end = start + per_page
        pnjs_on_page = filtered_data.iloc[start:end]
        print(f"PNJs on current page: {pnjs_on_page}")

        return jsonify({
            "pnjs": pnjs_on_page.to_dict(orient='records'),
            "total_pages": total_pages,
            "current_page": page
        })
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return jsonify({"error": str(e)})

# Route pour obtenir les races disponibles
@app.route('/get_races', methods=['POST'])
def get_races():
    try:
        races = pnj_data['Race'].unique().tolist()
        return jsonify(races)
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return jsonify({"error": str(e)})

# Route pour uploader une image de PNJ
@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        id = request.form.get('id')
        file = request.files.get('image')
        if file and id:
            id = int(id)
            os.makedirs('static/images/pnj', exist_ok=True)
            file_path = os.path.join('static/images/pnj', f'{id}.jpg')
            file.save(file_path)
            if id in pnj_data['Id'].values:
                pnj_data.loc[pnj_data['Id'] == id, 'Image'] = f'{id}.jpg'
                pnj_data.to_sql('pnj', get_db(), if_exists='replace', index=False)
                print(f"Image uploaded successfully for ID {id} and SQLite updated.")
                return jsonify({"success": True, "message": "Image uploaded successfully."})
            else:
                print(f"ID {id} not found in SQLite.")
                return jsonify({"success": False, "message": "ID not found in SQLite."})
        return jsonify({"success": False, "message": "No file or ID provided."})
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return jsonify({"error": str(e)})

# Route pour servir les images des PNJ
@app.route('/static/images/pnj/<filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/images/pnj'), filename)

# Exécution de l'application Flask
if __name__ == '__main__':
    try:
        # Vérifier si l'index existe, sinon le créer
        if not os.path.exists("indexdir"):
            print("L'index n'existe pas, création en cours...")
            create_whoosh_index()
        else:
            # Recréer l'index pour s'assurer qu'il est à jour
            print("Recréation de l'index pour s'assurer qu'il est à jour...")
            shutil.rmtree("indexdir")
            create_whoosh_index()
            
        app.run(debug=True)
    except Exception as e:
        print(f"Error running the app: {e}")