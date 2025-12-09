import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv
API_KEY = os.getenv("TMDB_API_KEY")
if not API_KEY:
    raise ValueError("❌ Error: Falta TMDB_API_KEY en el archivo .env")
CSV_FILE = "movies_clean.csv"

# -------------------
# Mapeo de géneros TMDB
# -------------------
GENRE_MAP = {
    28: "Acción",
    12: "Aventura",
    16: "Animación",
    35: "Comedia",
    80: "Crimen",
    99: "Documental",
    18: "Drama",
    10751: "Familiar",
    14: "Fantasía",
    36: "Historia",
    27: "Terror",
    10402: "Música",
    9648: "Misterio",
    10749: "Romance",
    878: "Ciencia ficción",
    10770: "Película de TV",
    53: "Suspenso",
    10752: "Bélica",
    37: "Western",
    10759: "Acción y Aventura",
    10762: "Infantil",
    10763: "Noticias",
    10764: "Reality",
    10765: "Sci-Fi y Fantasía",
    10766: "Telenovela",
    10767: "Talk Show",
    10768: "Guerra y Política"
}

def get_genre_names(genre_ids):
    """Convierte IDs de género a nombres legibles"""
    genres = [GENRE_MAP.get(gid, f"ID:{gid}") for gid in genre_ids]
    return ", ".join(genres) if genres else "Sin género"
 
# -------------------
# Funciones
# -------------------
def get_movies(page=1):
    url = f"{BASE_URL}/movie/popular?api_key={API_KEY}&language=es-ES&page={page}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else None
 
def get_series(page=1):
    url = f"{BASE_URL}/tv/popular?api_key={API_KEY}&language=es-ES&page={page}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else None
 
def get_platform(item_type, item_id):
    try:
        url = f"{BASE_URL}/{item_type}/{item_id}/watch/providers?api_key={API_KEY}"
        res = requests.get(url).json()
        # Intentar obtener providers de varios países
        for country in ['MX', 'US', 'ES']:
            providers = res['results'].get(country, {}).get('flatrate', [])
            if providers:
                return ', '.join([p['provider_name'] for p in providers])
        return "Desconocida"
    except:
        return "Desconocida"
 
def parse_movie(item):
    return {
        "title": item.get("title", ""),
        "year": item.get("release_date", "")[:4] if item.get("release_date") else "N/A",
        "type": "película",
        "genre": get_genre_names(item.get("genre_ids", [])),
        "platform": get_platform("movie", item.get("id")),
        "rating": round(item.get("vote_average", 0), 1),
        "overview": item.get("overview", "Sin descripción")[:200]  # Primeros 200 caracteres
    }
 
def parse_series(item):
    return {
        "title": item.get("name", ""),
        "year": item.get("first_air_date", "")[:4] if item.get("first_air_date") else "N/A",
        "type": "serie",
        "genre": get_genre_names(item.get("genre_ids", [])),
        "platform": get_platform("tv", item.get("id")),
        "rating": round(item.get("vote_average", 0), 1),
        "overview": item.get("overview", "Sin descripción")[:200]
    }
 
# -------------------
# Descargar datos
# -------------------
def main():
    peliculas, series = [], []
 
    print("Descargando películas...")
    for page in range(1, 40):  # Reducido a 50 páginas para ir más rápido
        print(f"  Página {page}/49 de películas...")
        data = get_movies(page)
        if data and "results" in data:
            for item in data["results"]:
                peliculas.append(parse_movie(item))
        time.sleep(0.3)  # Evitar rate limiting
 
    print("\nDescargando series...")
    for page in range(1, 400):
        print(f"  Página {page}/49 de series...")
        data = get_series(page)
        if data and "results" in data:
            for item in data["results"]:
                series.append(parse_series(item))
        time.sleep(0.3)
 
    df = pd.DataFrame(peliculas + series)
    df.drop_duplicates(subset="title", inplace=True)
    
    # Guardar con información adicional
    df.to_csv(CSV_FILE, index=False, encoding='utf-8')
    
    print(f"\n✅ Guardado en {CSV_FILE}")
    print(f"📊 Total registros: {len(df)}")
    print(f"🎬 Películas: {len(df[df['type'] == 'película'])}")
    print(f"📺 Series: {len(df[df['type'] == 'serie'])}")
    print(f"⭐ Calificación promedio: {df['rating'].mean():.1f}")
    
    # Mostrar muestra de datos
    print("\n📝 Muestra de datos:")
    print(df[['title', 'type', 'genre', 'platform', 'rating']].head(3))
 
if __name__ == "__main__":
    main()
