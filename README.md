# 🎬 CineClass Bot - Bot Recomendador de Películas y Series

Bot inteligente de Telegram que recomienda películas y series usando IA y algoritmos de similitud. Integra la API de TMDB para obtener información actualizada de contenido multimedia.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Características

- 🤖 **Chat con IA**: Conversaciones naturales usando Groq (LLaMA 3.3)
- 🎭 **Búsqueda por género**: Explora contenido por 18+ géneros diferentes
- 🎲 **Modo sorpresa**: Recomendaciones aleatorias
- 🔍 **Búsqueda directa**: Escribe el nombre de una película/serie
- 📊 **Filtros avanzados**: Por tipo (película/serie) y plataforma de streaming
- 🎯 **Recomendaciones similares**: Algoritmo TF-IDF para encontrar contenido relacionado
- 📜 **Historial**: Guarda tus búsquedas recientes
- 🎬 **Múltiples plataformas**: Netflix, Disney+, Amazon Prime, HBO Max, Apple TV+

## 📋 Requisitos

- Python 3.8 o superior
- Token de Bot de Telegram ([obtener en @BotFather](https://t.me/botfather))
- API Key de Groq ([obtener en console.groq.com](https://console.groq.com))
- API Key de TMDB ([obtener en themoviedb.org](https://www.themoviedb.org/settings/api)) *(opcional, solo para actualizar la base de datos)*

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/telegram-movie-recommender.git
cd telegram-movie-recommender
```

### 2. Crear entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y completa con tus credenciales:

```bash
cp .env.example .env
nano .env  # o usa tu editor favorito
```

Contenido del archivo `.env`:

```env
# Bot de Telegram
TELEGRAM_TOKEN=tu_token_de_telegram_aqui

# API de Groq para IA
GROQ_API_KEY=tu_api_key_de_groq_aqui

# API de TMDB (opcional, solo para fetch_tmdb.py)
TMDB_API_KEY=tu_api_key_de_tmdb_aqui
```

### 5. Descargar datos de TMDB (opcional)

Si quieres actualizar la base de datos de películas y series:

```bash
python fetch_tmdb.py
```

Esto generará el archivo `movies_clean.csv` con información actualizada.

**Nota:** El repositorio ya incluye una base de datos pre-descargada, por lo que este paso es opcional.

### 6. Ejecutar el bot

```bash
python bot.py
```

Deberías ver:
```
✅ Contenido cargado y matriz TF-IDF lista. Total registros: 8564
✅ Bot CineClass iniciado correctamente. Esperando mensajes...
```

## 📁 Estructura del Proyecto

```
telegram-movie-recommender/
├── bot.py              # Lógica principal del bot
├── utils_db.py         # Funciones de recomendación (TF-IDF)
├── fetch_tmdb.py       # Script para descargar datos de TMDB
├── movies_clean.csv    # Base de datos de películas y series (no incluido en repo)
├── .env                # Variables de entorno (NO SUBIR A GIT)
├── .env.example        # Plantilla de variables de entorno
├── .gitignore          # Archivos ignorados por Git
├── requirements.txt    # Dependencias de Python
└── README.md           # Este archivo
```

## 🎮 Uso del Bot

### Comandos disponibles

- `/start` - Menú principal
- `/help` - Guía de uso
- `/random` - Recomendación aleatoria
- `/filter` - Buscar con filtros
- `/history` - Ver tu historial

### Modos de uso

1. **Búsqueda por género**: Click en "Buscar contenido" → Selecciona género → Explora títulos
2. **Búsqueda directa**: Escribe el nombre de una película/serie (ej: "Spider-Man")
3. **Chat con IA**: Conversa naturalmente sobre cine y TV
4. **Modo sorpresa**: Click en "Sorpréndeme" para recomendaciones aleatorias

## 🛠️ Tecnologías Utilizadas

- **[python-telegram-bot](https://python-telegram-bot.org/)**: Framework para bots de Telegram
- **[Groq](https://groq.com/)**: API de IA para chat inteligente (LLaMA 3.3)
- **[scikit-learn](https://scikit-learn.org/)**: Algoritmo TF-IDF para recomendaciones
- **[pandas](https://pandas.pydata.org/)**: Procesamiento de datos
- **[TMDB API](https://www.themoviedb.org/documentation/api)**: Base de datos de películas y series
- **[NLTK](https://www.nltk.org/)**: Procesamiento de lenguaje natural

## 🔧 Configuración Avanzada

### Personalizar géneros

Edita la lista `GENRES` en `bot.py`:

```python
GENRES = [
    "Acción", "Aventura", "Animación", "Comedia", 
    # Agrega más géneros aquí
]
```

### Cambiar cantidad de recomendaciones

En `bot.py`, modifica el parámetro `top_n`:

```python
recomendaciones = recomendar_contenido(item['title'], top_n=15)  # Cambia 15 por el número deseado
```

### Actualizar base de datos

Para obtener más películas/series, modifica los rangos en `fetch_tmdb.py`:

```python
for page in range(1, 100):  # Aumenta el número de páginas
```

## 📊 Características de la Base de Datos

La base de datos incluye:
- 🎬 Películas populares
- 📺 Series populares
- 🎭 18+ géneros diferentes
- ⭐ Calificaciones de usuarios
- 🎯 Plataformas de streaming disponibles
- 📝 Sinopsis de cada título

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para cambios importantes:

1. Fork el proyecto
2. Crea una rama para tu función (`git checkout -b feature/nueva-funcion`)
3. Commit tus cambios (`git commit -m 'Agregar nueva función'`)
4. Push a la rama (`git push origin feature/nueva-funcion`)
5. Abre un Pull Request

## 📝 Notas Importantes

- **Seguridad**: Nunca subas tu archivo `.env` a repositorios públicos
- **Rate Limiting**: La API de TMDB tiene límites de peticiones. `fetch_tmdb.py` incluye delays para evitarlos
- **Base de datos**: El archivo `movies_clean.csv` puede ser grande (>1MB). Considera no incluirlo en el repositorio y documentar cómo generarlo

## 🐛 Solución de Problemas

### Error: "Conflict: terminated by other getUpdates request"
Hay otra instancia del bot corriendo. Detén todos los procesos:
```bash
pkill -f bot.py
```

### Error: "No module named 'dotenv'"
Instala las dependencias:
```bash
pip install python-dotenv
```

### Error: "ValueError: Falta archivo .env"
Asegúrate de crear el archivo `.env` con tus credenciales.


**Tu Nombre** - [GitHub](https://github.com/TU_USUARIO)

## 🙏 Agradecimientos

- [TMDB](https://www.themoviedb.org/) por proporcionar la API de películas y series
- [Groq](https://groq.com/) por la API de IA gratuita
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) por el excelente framework


---

⭐ Si te gusta este proyecto, ¡dale una estrella en GitHub!
