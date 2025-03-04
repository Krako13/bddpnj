import os, shutil, unicodedata
import nltk, spacy
from whoosh.fields import Schema, ID, TEXT
from whoosh.analysis import Analyzer, Token
from whoosh.qparser import MultifieldParser, OrGroup
from flask import current_app
from modules.pnj_model import get_pnj_data
from modules.synonyms import expanded_synonyms


nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

try:
    nlp = spacy.load('fr_core_news_sm')
except Exception as e:
    spacy.cli.download('fr_core_news_sm')
    nlp = spacy.load('fr_core_news_sm')

def clean_text(text):
    if text:
        text = text.replace('"', '«').replace("'", "’")
        text = unicodedata.normalize('NFC', text)
        return text
    return ''

class FrenchAnalyzer(Analyzer):
    def __init__(self):
        self.stopwords = set(nltk.corpus.stopwords.words('french'))
    def __call__(self, value, **kwargs):
        value = clean_text(value)
        doc = nlp(value)
        position = 0
        for i, token in enumerate(doc):
            if token.is_stop or token.is_space:
                continue
            if token.is_punct and token.text not in ["'", "’"]:
                continue
            word = token.lemma_.lower()
            t = Token(pos=i, startchar=position, endchar=position + len(token.text),
                      removestops=True, mode="index", text=word)
            yield t
            if word in expanded_synonyms:
                for synonym in expanded_synonyms[word]:
                    t_syn = Token(pos=i, startchar=position, endchar=position + len(token.text),
                                  removestops=True, mode="index", text=synonym)
                    yield t_syn
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

try:
    custom_analyzer = FrenchAnalyzer()
    print("Using custom analyzer with synonyms and gender handling")
except Exception as e:
    print(f"Error with custom analyzer: {e}")
    from whoosh.analysis import StemmingAnalyzer
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

def create_whoosh_index():
    INDEX_DIR = current_app.config['INDEX_DIR']
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    else:
        shutil.rmtree(INDEX_DIR)
        os.mkdir(INDEX_DIR)
    from whoosh import index as whoosh_index
    ix = whoosh_index.create_in(INDEX_DIR, schema)
    writer = ix.writer()
    data = get_pnj_data()
    print(f"Nombre de PNJ à indexer: {len(data)}")
    for _, row in data.iterrows():
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
