from flask import Flask, render_template, request, jsonify, send_from_directory, g
import pandas as pd
import nltk
import spacy
from whoosh.fields import Schema, ID, TEXT
from whoosh.analysis import Analyzer, Token
from whoosh import index as whoosh_index
from whoosh.qparser import MultifieldParser, OrGroup
import os
import math
import sqlite3
import numpy as np
import re
import shutil
import unicodedata

# Définition des chemins indépendants du système
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'bddpnj.db')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
STATIC_IMAGES_PNJ_DIR = os.path.join(STATIC_DIR, 'images', 'pnj')
INDEX_DIR = os.path.join(BASE_DIR, 'indexdir')

# Extensions autorisées pour l'upload des images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Télécharger les ressources nécessaires pour NLTK
try:
    nltk.download('wordnet')
    nltk.download('omw-1.4')  # Ressources multilingues pour WordNet
    nltk.download('stopwords')
    print("NLTK resources downloaded successfully.")
except Exception as e:
    print(f"Error downloading NLTK resources: {e}")

# Charger le modèle spaCy pour le français
try:
    nlp = spacy.load('fr_core_news_sm')
    print("spaCy model loaded successfully.")
except Exception as e:
    print(f"Error loading spaCy model: {e}")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
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
    "Marché": "PNJ que l'on peut rencontrer dans des lieux publics, comme les marchés ou les places de village. Ces endroits sont propices aux rencontres et aux échanges commerciaux.",
    "Bibliothèque Ancienne": "PNJ que l'on peut rencontrer dans des lieux de savoir ancien, comme les bibliothèques ou les archives. Ces personnages sont souvent des érudits ou des gardiens de connaissances oubliées.",
    "Château/Palais": "PNJ que l'on peut rencontrer dans des lieux de pouvoir, comme les châteaux ou les palais. Ces personnages sont souvent des nobles, des conseillers ou des gardes royaux.",
    "Guilde/Atelier": "PNJ que l'on peut rencontrer dans des lieux de travail, comme les guildes ou les ateliers d'artisans. Ces personnages sont souvent des artisans, des marchands, ou des membres de guildes.",
    "Militaire": "PNJ que l'on peut rencontrer dans des contextes militaires, comme les camps d'entraînement ou les forteresses. Ces personnages sont souvent des soldats, des officiers, ou des stratèges.",
    "Port/Quai": "PNJ que l'on peut rencontrer dans des lieux maritimes, comme les ports ou les quais. Ces personnages sont souvent des marins, des pêcheurs, ou des marchands.",
    "Temple/Église": "PNJ que l'on peut rencontrer dans des lieux sacrés, comme les temples ou les églises. Ces personnages sont souvent des prêtres, des moines, ou des fidèles.",
    "Rue/Place Publique": "PNJ que l'on peut rencontrer dans les rues ou les places publiques des villes et villages. Ces endroits sont animés et propices aux rencontres fortuites."
}

# Dictionnaire de synonymes pour améliorer la recherche
synonyms = {
    # Métiers et rôles
    "marchand": ["commerçant", "vendeur", "négociant", "boutiquier", "mercanti"],
    "guerrier": ["combattant", "soldat", "militaire", "spadassin", "homme d'armes"],
    "guerrière": ["combattante", "soldate", "militaire", "femme d'armes"],
    "mage": ["magicien", "sorcier", "enchanteur", "thaumaturge", "occultiste"],
    "magicienne": ["sorcière", "enchanteresse", "thaumaturge", "occultiste"],
    "voleur": ["brigand", "bandit", "malfrat", "larron", "cambrioleur", "pickpocket"],
    "voleuse": ["brigande", "bandite", "malfrate", "larronne", "cambrioleuse"],
    "noble": ["aristocrate", "seigneur", "gentilhomme", "patricien"],
    "prêtre": ["clerc", "ecclésiastique", "religieux", "homme d'église", "pasteur"],
    "prêtresse": ["religieuse", "femme d'église"],
    "fermier": ["paysan", "agriculteur", "cultivateur", "métayer"],
    "fermière": ["paysanne", "agricultrice", "cultivatrice", "métayère"],
    # Lieux
    "taverne": ["auberge", "estaminet", "bistrot", "brasserie", "débit de boisson"],
    "forêt": ["bois", "bosquet", "futaie", "sylve"],
    "marché": ["foire", "bazar", "halle", "étal", "échoppe"],
    "château": ["palais", "forteresse", "citadelle", "donjon", "bastide"],
    "temple": ["église", "sanctuaire", "lieu saint", "chapelle", "cathédrale"],
    "bibliothèque": ["archives", "salle d'étude", "manuscrits", "collection"],
    # Races fantasy communes
    "humain": ["homme", "personne", "individu"],
    "humaine": ["femme", "personne", "individue"],
    "elfe": ["sylvain", "haut-elfe", "elfe des bois", "elfe sylvestre"],
    "nain": ["peuple des montagnes", "forgeron"],
    "orc": ["demi-orc", "goblinoïde", "peau-verte"],
    "halfelin": ["semi-homme", "petit peuple", "hobbit"]
}

# Conversion en dictionnaire pour l'analyseur
expanded_synonyms = {}
for word, syn_list in synonyms.items():
    for syn in syn_list:
        if syn not in expanded_synonyms:
            expanded_synonyms[syn] = []
        expanded_synonyms[syn].append(word)
    expanded_synonyms[word] = syn_list

# Fonction de nettoyage du texte pour gérer les caractères spéciaux
def clean_text(text):
    if text:
        # Remplacer les guillemets et apostrophes par leur version typographique
        text = text.replace('"', '«').replace("'", "’")
        # Normaliser le texte en Unicode NFC
        text = unicodedata.normalize('NFC', text)
        return text
    else:
        return ''

# Créer un analyseur personnalisé avec support pour les synonymes et gestion des genres
class FrenchAnalyzer(Analyzer):
    def __init__(self):
        self.stopwords = set(nltk.corpus.stopwords.words('french'))
        
    def __call__(self, value, **kwargs):
        # Nettoyer le texte avant la tokenisation
        value = clean_text(value)
        
        # Tokenization avec spaCy
        doc = nlp(value)
        
        # Générer des tokens
        position = 0
        for i, token in enumerate(doc):
            if token.is_stop or token.is_space:
                continue
            if token.is_punct and token.text not in ["'", "’"]:
                continue
                
            # Normaliser et filtrer
            word = token.lemma_.lower()
            
            # Créer token Whoosh
            t = Token(pos=i, startchar=position, endchar=position + len(token.text), 
                      removestops=True, mode="index", text=word)
            # Ajouter le token original
            yield t
            
            # Ajouter les synonymes si disponibles
            if word in expanded_synonyms:
                for synonym in expanded_synonyms[word]:
                    t_syn = Token(pos=i, startchar=position, endchar=position + len(token.text),
                                  removestops=True, mode="index", text=synonym)
                    yield t_syn
                
            # Gérer le genre (masculin/féminin)
            if word.endswith('e') and len(word) > 3:
                masculine = word[:-1]
                t_masc = Token(pos=i, startchar=position, endchar=position + len(token.text),
                               removestops=True, mode="index", text=masculine)
                yield t_masc
            elif not word.endswith('e') and len(word) > 3:
                feminine = word + 'e'
                t_fem = Token(pos=i, startchar=position, endchar=position + len(token.text),
                              removestops=True, mode="index", text=feminine)
                yield t_fem
                    
            position += len(token.text) + 1

# Créer le schéma pour Whoosh
try:
    # Créer notre analyseur personnalisé
    custom_analyzer = FrenchAnalyzer()
    print("Using custom analyzer with synonyms and gender handling")
except Exception as e:
    print(f"Error with custom analyzer: {e}")
    # Fallback sur StemmingAnalyzer
    custom_analyzer = StemmingAnalyzer(lang='french')
    print("Using StemmingAnalyzer for French")

schema = Schema(
    id=ID(unique=True, stored=True),
    nom=TEXT(stored=True, analyzer=custom_analyzer),
    description=TEXT(stored=True, analyzer=custom_analyzer),
    categorie=TEXT(stored=True, analyzer=custom_analyzer),
    sexe=TEXT(stored=True),
    race=TEXT(stored=True, analyzer=custom_analyzer)
)

# Créer l'index Whoosh
def create_whoosh_index():
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    else:
        # Recréer l'index pour s'assurer qu'il est à jour
        shutil.rmtree(INDEX_DIR)
        os.mkdir(INDEX_DIR)
    ix = whoosh_index.create_in(INDEX_DIR, schema)
    writer = ix.writer()
    
    print(f"Nombre de PNJ à indexer: {len(pnj_data)}")
    for _, row in pnj_data.iterrows():
        try:
            nom = clean_text(row['Nom'])
            description = clean_text(row['Description'])
            categorie = clean_text(row['Catégorie'])
            race = clean_text(row['Race'])
            
            writer.add_document(
                id=str(row['Id']),
                nom=nom,
                description=description,
                categorie=categorie,
                sexe=row['Sexe'],
                race=race
            )
            print(f"Indexed: {nom}")
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

# Fonction pour effectuer la recherche avancée
def perform_advanced_search(keyword, searcher):
    # Champs à rechercher
    fields = ['nom', 'description', 'categorie', 'race']
    
    # Créer un parser qui utilise des OR entre les termes au lieu de AND par défaut
    parser = MultifieldParser(fields, schema=searcher.schema, group=OrGroup.factory(0.9))
    
    # Préparer les mots-clés pour la recherche
    keyword = keyword.lower().strip()
    
    # Traitement spaCy pour meilleure compréhension
    doc = nlp(keyword)
    
    # Extraire les lemmes et formes de base
    lemmas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    
    # Si le mot est dans notre dictionnaire de synonymes, ajouter les synonymes
    expanded_terms = []
    for lemma in lemmas:
        expanded_terms.append(lemma)
        if lemma in expanded_synonyms:
            expanded_terms.extend(expanded_synonyms[lemma])
    
    # Créer la requête de recherche
    if expanded_terms:
        # Joindre avec OR pour une recherche plus flexible
        search_terms = " OR ".join(expanded_terms)
        print(f"Expanded search terms: {search_terms}")
        
        try:
            query = parser.parse(search_terms)
            print(f"Query: {query}")
            return searcher.search(query, limit=None)
        except Exception as e:
            print(f"Erreur avec la requête étendue: {e}")
    
    # Si la recherche étendue échoue, essayer une approche plus basique
    try:
        # Essayer directement
        query = parser.parse(keyword)
        results = searcher.search(query, limit=None)
        
        # Si aucun résultat, essayer avec caractères jokers
        if len(results) == 0:
            keyword_with_wildcard = f"*{keyword}*"
            query = parser.parse(keyword_with_wildcard)
            print(f"Trying with wildcard query: {query}")
            results = searcher.search(query, limit=None)
        
        return results
    except Exception as e:
        print(f"Erreur lors de la recherche: {e}")
        return []

# Route pour la page d'accueil
@app.route('/')
def home():
    return render_template('home.html')

# Route pour la table des PNJ
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

        # Commencer avec toutes les données
        filtered_data = pnj_data.copy()

        # Filtrer par sexe et race si sélectionnés
        if sexe:
            filtered_data = filtered_data[filtered_data['Sexe'] == sexe]
        if race:
            filtered_data = filtered_data[filtered_data['Race'] == race]
        print(f"Filtered data after sexe and race filter: {len(filtered_data)} records")

        # Filtrer par localisation (Catégorie) si sélectionnée
        if category:
            filtered_data = filtered_data[filtered_data['Catégorie'] == category]
            print(f"Filtered data after category filter: {len(filtered_data)} records")
        else:
            print(f"No category filter provided, using all localisations")

        # Si on demande un PNJ aléatoire, on coupe le DataFrame après tous les filtrages
        if action == 'random':
            if not filtered_data.empty:
                filtered_data = filtered_data.sample(n=1)
                print("Filtered data after random selection:")
                print(filtered_data)
            else:
                print("Aucun PNJ trouvé après application des filtres.")
        elif keyword:
            print(f"Searching for: {keyword}")
            try:
                # Ouvrir l'index Whoosh
                ix = whoosh_index.open_dir(INDEX_DIR)
                with ix.searcher() as searcher:
                    # Effectuer la recherche avancée
                    results = perform_advanced_search(keyword, searcher)
                    ids = [int(hit['id']) for hit in results]
                    print(f"Search results: {len(ids)} matches")
                    
                    # Filtrer les données originales par la recherche
                    filtered_data = filtered_data[filtered_data['Id'].isin(ids)]
                    print(f"Filtered data after keyword search: {len(filtered_data)} records")
            except Exception as e:
                print(f"Erreur lors de la recherche Whoosh: {e}")
                if not os.path.exists(INDEX_DIR):
                    print("L'index n'existe pas, création en cours...")
                    create_whoosh_index()
        else:
            print(f"No keyword provided, using unfiltered data: {len(filtered_data)} records")

        # Calculer le nombre total de pages
        total_pages = max(1, math.ceil(len(filtered_data) / per_page))
        print(f"Total pages: {total_pages}")

        # Obtenir les PNJ pour la page actuelle
        start = (page - 1) * per_page
        end = start + per_page
        pnjs_on_page = filtered_data.iloc[start:end]
        print(f"PNJs on current page: {len(pnjs_on_page)} records")

        return render_template('pnj.html',
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
        print(f"Filtered data after sexe and race filter: {len(filtered_data)} records")
        if category:
            filtered_data = filtered_data[filtered_data['Catégorie'] == category]
        print(f"Filtered data after category filter: {len(filtered_data)} records")
        if action == 'random':
            filtered_data = filtered_data.sample(n=1)
            print(f"Filtered data after random selection: {filtered_data}")
        elif keyword:
            print(f"Searching for: {keyword}")
            try:
                # Ouvrir l'index Whoosh
                ix = whoosh_index.open_dir(INDEX_DIR)
                with ix.searcher() as searcher:
                    # Effectuer la recherche avancée
                    results = perform_advanced_search(keyword, searcher)
                    ids = [int(hit['id']) for hit in results]
                    print(f"Search results: {len(ids)} matches")
                    
                    # Filtrer les données originales
                    filtered_data = filtered_data[filtered_data['Id'].isin(ids)]
                    print(f"Filtered data after search: {len(filtered_data)} records")
            except Exception as e:
                print(f"Erreur lors de la recherche Whoosh: {e}")
                # Si l'index n'existe pas, le créer
                if not os.path.exists(INDEX_DIR):
                    print("L'index n'existe pas, création en cours...")
                    create_whoosh_index()
        else:
            print(f"No keyword provided, using unfiltered data: {len(filtered_data)} records")

        # Filtrer par catégorie si sélectionnée
        if category:
            filtered_data = filtered_data[filtered_data['Catégorie'] == category]
            print(f"Filtered data after category filter: {len(filtered_data)} records")

        # Calculer le nombre total de pages
        total_pages = max(1, math.ceil(len(filtered_data) / per_page))
        print(f"Total pages: {total_pages}")

        # Obtenir les PNJ pour la page actuelle
        start = (page - 1) * per_page
        end = start + per_page
        pnjs_on_page = filtered_data.iloc[start:end]
        print(f"PNJs on current page: {len(pnjs_on_page)} records")

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
            if allowed_file(file.filename):
                id = int(id)
                os.makedirs(STATIC_IMAGES_PNJ_DIR, exist_ok=True)
                filename = f'{id}.jpg'
                file_path = os.path.join(STATIC_IMAGES_PNJ_DIR, filename)
                file.save(file_path)
                if id in pnj_data['Id'].values:
                    pnj_data.loc[pnj_data['Id'] == id, 'Image'] = filename
                    pnj_data.to_sql('pnj', get_db(), if_exists='replace', index=False)
                    print(f"Image uploaded successfully for ID {id} and SQLite updated.")
                    return jsonify({"success": True, "message": "Image uploaded successfully."})
                else:
                    print(f"ID {id} not found in SQLite.")
                    return jsonify({"success": False, "message": "ID not found in SQLite."})
            else:
                return jsonify({"success": False, "message": "Type de fichier non autorisé."})
        return jsonify({"success": False, "message": "Aucun fichier ou ID fourni."})
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return jsonify({"error": str(e)})

# Route pour servir les images des PNJ
@app.route('/static/images/pnj/<filename>')
def serve_image(filename):
    response = send_from_directory(STATIC_IMAGES_PNJ_DIR, filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# Exécution de l'application Flask
if __name__ == '__main__':
    try:
        # Vérifier si l'index existe, sinon le créer
        if not os.path.exists(INDEX_DIR):
            print("L'index n'existe pas, création en cours...")
            create_whoosh_index()
        else:
            # Recréer l'index pour s'assurer qu'il est à jour avec l'analyseur personnalisé
            print("Recréation de l'index avec l'analyseur amélioré...")
            create_whoosh_index()
                
        app.run(debug=True)
    except Exception as e:
        print(f"Error running the app: {e}")
