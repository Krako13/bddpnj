import pandas as pd
from modules.database import get_db
from modules.search import FrenchAnalyzer
def get_pnj_data():
    """
    Récupère et renvoie les données de la table 'pnj' de la base de données
    sous forme de DataFrame pandas.
    Cette fonction est appelée au sein d'un contexte d'application.
    """
    conn = get_db()
    query = "SELECT * FROM pnj"
    df = pd.read_sql_query(query, conn)
    return df

# Vos autres constantes et fonctions (par exemple, category_descriptions et perform_advanced_search)
# Si vous avez d'autres données comme category_descriptions, vous pouvez les définir ici,
# car ce sont simplement des dictionnaires et ne dépendent pas d'un contexte.
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

# Vous pouvez également inclure ici la fonction perform_advanced_search si elle n'accède pas à current_app au niveau global.
# Si elle dépend de current_app, assurez-vous de l'appeler uniquement dans vos routes.
def perform_advanced_search(keyword, searcher):
    from whoosh.qparser import MultifieldParser, OrGroup
    fields = ['nom', 'description', 'categorie', 'race']
    parser = MultifieldParser(fields, schema=searcher.schema, group=OrGroup.factory(0.9))
    keyword = keyword.lower().strip()
    doc = nlp(keyword)
    lemmas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    expanded_terms = []
    for lemma in lemmas:
        expanded_terms.append(lemma)
        if lemma in expanded_synonyms:
            expanded_terms.extend(expanded_synonyms[lemma])
    if expanded_terms:
        search_terms = " OR ".join(expanded_terms)
        print(f"Expanded search terms: {search_terms}")
        try:
            query = parser.parse(search_terms)
            print(f"Query: {query}")
            results = searcher.search(query, limit=None)
            return results
        except Exception as e:
            print(f"Erreur avec la requête étendue: {e}")
    try:
        query = parser.parse(keyword)
        results = searcher.search(query, limit=None)
        if len(results) == 0:
            keyword_with_wildcard = f"*{keyword}*"
            query = parser.parse(keyword_with_wildcard)
            print(f"Trying with wildcard query: {query}")
            results = searcher.search(query, limit=None)
        return results
    except Exception as e:
        print(f"Erreur lors de la recherche: {e}")
        return []