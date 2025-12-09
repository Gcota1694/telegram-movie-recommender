# utils_db.py
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

# Variables globales
contenido = None
tfidf_matrix = None
tfidf_vectorizer = None

def cargar_contenido(csv_file="movies_clean.csv"):
    """
    Carga el CSV y prepara la matriz TF-IDF para recomendaciones.
    Solo usa el título para TF-IDF, ya que el CSV actual no tiene géneros.
    """
    global contenido, tfidf_matrix, tfidf_vectorizer

    contenido = pd.read_csv(csv_file)

    if contenido.empty:
        raise ValueError("El CSV está vacío.")

    # Creamos 'overview' solo con el título
    contenido['overview'] = contenido['title'].astype(str)

    # Vectorización TF-IDF
    tfidf_vectorizer = TfidfVectorizer(stop_words=stopwords.words('spanish'))
    tfidf_matrix = tfidf_vectorizer.fit_transform(contenido['overview'])

    print(f"✅ Contenido cargado y matriz TF-IDF lista. Total registros: {len(contenido)}")
    return contenido, tfidf_matrix

def recomendar_contenido(nombre, top_n=5):
    """
    Devuelve una lista de recomendaciones basadas en el título ingresado.
    """
    if contenido is None or tfidf_matrix is None:
        raise ValueError("Primero debes cargar el contenido usando cargar_contenido()")

    nombre = nombre.lower()
    matches = contenido[contenido['title'].str.lower().str.contains(nombre)]

    if matches.empty:
        return []

    # Tomamos el primer match
    idx = matches.index[0]

    cosine_similarities = linear_kernel(tfidf_matrix[idx], tfidf_matrix).flatten()
    related_indices = cosine_similarities.argsort()[-top_n-1:-1][::-1]

    recomendaciones = []
    for i in related_indices:
        row = contenido.iloc[i]
        recomendaciones.append({
            "title": row['title'],
            "type": row['type'],
            "platform": row['platform']
        })

    return recomendaciones
