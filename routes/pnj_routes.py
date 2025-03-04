from flask import Blueprint, render_template, request, jsonify, current_app
from modules.pnj_model import get_pnj_data, category_descriptions
from modules.search import perform_advanced_search, create_whoosh_index
import math, os

pnj_bp = Blueprint('pnj_bp', __name__)

@pnj_bp.route('/pnj', methods=['GET', 'POST'])
def pnj_table():
    try:
        # Récupération des données de la table 'pnj'
        data = get_pnj_data()

        category = request.args.get('category', '')
        keyword = request.args.get('keyword', '').lower()
        sexe = request.args.get('sexe', '')
        race = request.args.get('race', '')
        action = request.args.get('action', 'filter')
        page = int(request.args.get('page', 1))
        per_page = 9

        print(f"Requête PNJ reçu: keyword={keyword}, category={category}, sexe={sexe}, race={race}, action={action}")
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
                print("PNJ aléatoire sélectionné.")
        elif keyword:
            print(f"Recherche pour: {keyword}")
            try:
                from whoosh import index as whoosh_index
                ix = whoosh_index.open_dir(current_app.config['INDEX_DIR'])
                with ix.searcher() as searcher:
                    results = perform_advanced_search(keyword, searcher)
                    ids = [int(hit['id']) for hit in results]
                    print(f"{len(ids)} correspondances trouvées.")
                    filtered_data = filtered_data[filtered_data['Id'].isin(ids)]
            except Exception as e:
                print(f"Erreur lors de la recherche Whoosh: {e}")
                if not os.path.exists(current_app.config['INDEX_DIR']):
                    create_whoosh_index()
        else:
            print("Aucun critère de recherche fourni. Affichage de toutes les données.")

        total_pages = max(1, math.ceil(len(filtered_data) / per_page))
        print(f"Total pages: {total_pages}")
        start = (page - 1) * per_page
        end = start + per_page
        pnjs_on_page = filtered_data.iloc[start:end]
        print(f"{len(pnjs_on_page)} PNJ(s) affiché(s) sur la page {page}")

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
        print(f"Une erreur s'est produite dans pnj_table: {e}")
        return f"Une erreur s'est produite : {e}"

@pnj_bp.route('/get_data', methods=['POST'])
def get_data():
    try:
        data = get_pnj_data()
        category = request.form.get('category', '')
        keyword = request.form.get('keyword', '').lower()
        sexe = request.form.get('sexe', '')
        race = request.form.get('race', '')
        action = request.form.get('action', 'filter')
        page = int(request.form.get('page', 1))
        per_page = 9

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
            print(f"Recherche pour: {keyword}")
            try:
                from whoosh import index as whoosh_index
                ix = whoosh_index.open_dir(current_app.config['INDEX_DIR'])
                with ix.searcher() as searcher:
                    results = perform_advanced_search(keyword, searcher)
                    ids = [int(hit['id']) for hit in results]
                    filtered_data = filtered_data[filtered_data['Id'].isin(ids)]
            except Exception as e:
                print(f"Erreur lors de la recherche Whoosh: {e}")
                if not os.path.exists(current_app.config['INDEX_DIR']):
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
        print(f"Une erreur s'est produite dans get_data: {e}")
        return jsonify({"error": str(e)})

@pnj_bp.route('/get_races', methods=['POST'])
def get_races():
    try:
        data = get_pnj_data()
        races = data['Race'].unique().tolist()
        return jsonify(races)
    except Exception as e:
        print(f"Une erreur s'est produite dans get_races: {e}")
        return jsonify({"error": str(e)})
