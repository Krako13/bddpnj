# modules/synonyms.py

synonyms = {
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
    "taverne": ["auberge", "estaminet", "bistrot", "brasserie", "débit de boisson"],
    "forêt": ["bois", "bosquet", "futaie", "sylve"],
    "marché": ["foire", "bazar", "halle", "étal", "échoppe"],
    "château": ["palais", "forteresse", "citadelle", "donjon", "bastide"],
    "temple": ["église", "sanctuaire", "lieu saint", "chapelle", "cathédrale"],
    "bibliothèque": ["archives", "salle d'étude", "manuscrits", "collection"],
    "humain": ["homme", "personne", "individu"],
    "humaine": ["femme", "personne", "individue"],
    "elfe": ["sylvain", "haut-elfe", "elfe des bois", "elfe sylvestre"],
    "nain": ["peuple des montagnes", "forgeron"],
    "orc": ["demi-orc", "goblinoïde", "peau-verte"],
    "halfelin": ["semi-homme", "petit peuple", "hobbit"]
}

expanded_synonyms = {}
for word, syn_list in synonyms.items():
    for syn in syn_list:
        if syn not in expanded_synonyms:
            expanded_synonyms[syn] = []
        expanded_synonyms[syn].append(word)
    expanded_synonyms[word] = syn_list
