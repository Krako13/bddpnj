import pandas as pd
from modules.database import get_db

def get_pnj_data():
    """
    Récupère et retourne les données de la table 'pnj' sous forme d'un DataFrame.
    Doit être appelée dans le contexte d'une requête.
    """
    conn = get_db()
    query = "SELECT * FROM pnj"
    df = pd.read_sql_query(query, conn)
    return df

# Constantes : descriptions des catégories
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
