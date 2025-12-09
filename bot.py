import logging
import random
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from utils_db import cargar_contenido, recomendar_contenido
import utils_db
import pandas as pd
from groq import Groq

# Cargar variables de entorno
load_dotenv()

# -------------------
# Configuración
# -------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Verificar que las variables se cargaron
if not TOKEN or not GROQ_API_KEY:
    raise ValueError("❌ Falta archivo .env con TELEGRAM_TOKEN y GROQ_API_KEY")

# Cliente Groq
groq_client = Groq(api_key=GROQ_API_KEY)

# Estados de conversación
CHOOSING_TYPE, CHOOSING_GENRE, CHOOSING_PLATFORM = range(3)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Historial de usuarios
user_history = {}

# Lista de géneros disponibles
GENRES = [
    "Acción", "Aventura", "Animación", "Comedia", "Crimen",
    "Documental", "Drama", "Familiar", "Fantasía", "Historia",
    "Terror", "Música", "Misterio", "Romance", "Ciencia ficción",
    "Suspenso", "Bélica", "Western"
]

# -------------------
# Función de IA con Groq
# -------------------
def chat_with_ai(user_message, conversation_history=None):
    """Chat con IA usando Groq (100% GRATIS)"""
    try:
        messages = [
            {
                "role": "system",
                "content": """Eres CineClass Bot, un asistente amigable y experto en películas y series.
                Tu trabajo es ayudar a los usuarios a encontrar contenido para ver y mantener 
                conversaciones entretenidas sobre cine y TV. Sé conciso (máximo 3-4 líneas), 
                amigable y usa emojis ocasionalmente. Si te preguntan sobre recomendaciones 
                específicas de títulos, sugiere que escriban el nombre de la película/serie o 
                usen los botones del bot para explorar."""
            }
        ]
        
        if conversation_history:
            messages.extend(conversation_history[-10:])
        
        messages.append({"role": "user", "content": user_message})
        
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",  # MODELO ACTUALIZADO
            temperature=0.7,
            max_tokens=200,
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error en Groq: {error_msg}")
        
        # Mensajes de error más específicos
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return "🔑 Error de autenticación con la IA. El administrador necesita verificar la API key. Mientras tanto, ¿qué película o serie buscas? 🎬"
        elif "rate_limit" in error_msg.lower():
            return "⏰ Demasiadas consultas. Espera un momento e intenta de nuevo. Mientras, puedes buscar películas escribiendo el nombre 🎬"
        else:
            return "Hmm, tuve un problema técnico 🤔 Pero puedo ayudarte! Escribe el nombre de una película/serie o usa los botones para explorar 🎬"

# -------------------
# Comandos básicos
# -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Buscar contenido", callback_data='browse_genres')],
        [InlineKeyboardButton("🎲 Sorpréndeme", callback_data='random')],
        [InlineKeyboardButton("📊 Filtrar por criterios", callback_data='filter')],
        [InlineKeyboardButton("📜 Mi historial", callback_data='history')],
        [InlineKeyboardButton("❓ Ayuda", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "¡Hola! Soy CineClass Bot 🎬🤖\n\n"
        "Puedo ayudarte a encontrar películas y series perfectas para ti.\n"
        "¿Qué te gustaría hacer?",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🎬 **CineClass Bot - Guía de uso**

**Comandos:**
/start - Menú principal
/help - Esta ayuda
/random - Recomendación aleatoria
/filter - Buscar con filtros
/history - Ver tu historial

**Modos de uso:**
1️⃣ **Búsqueda por género**: Explora por géneros y descubre títulos
2️⃣ **Búsqueda directa**: Escribe el nombre de una película/serie
3️⃣ **Menú interactivo**: Usa los botones para navegar
4️⃣ **Chat con IA**: Conversa sobre cine y TV

**Ejemplos:**
- Click en "Buscar contenido" → Elige género → Ve títulos → Detalles
- "Spider-Man"
- "Hola, ¿qué opinas de Marvel?"
    """
    
    if update.callback_query:
        await update.callback_query.message.reply_text(help_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(help_text, parse_mode='Markdown')

# -------------------
# Navegación por géneros
# -------------------
async def browse_genres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if utils_db.contenido is None or utils_db.contenido.empty:
        await query.message.edit_text(
            "❌ No hay contenido cargado. Por favor, ejecuta primero el script de descarga.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Menú principal", callback_data='menu')
            ]])
        )
        return
    
    keyboard = []
    for i in range(0, len(GENRES), 2):
        row = []
        row.append(InlineKeyboardButton(f"🎭 {GENRES[i]}", callback_data=f'genre_{GENRES[i]}'))
        if i + 1 < len(GENRES):
            row.append(InlineKeyboardButton(f"🎭 {GENRES[i+1]}", callback_data=f'genre_{GENRES[i+1]}'))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🏠 Menú principal", callback_data='menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "🎬 **Selecciona un género:**\n\n"
        "Elige el tipo de contenido que te gustaría explorar:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_titles_by_genre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    genre = query.data.replace('genre_', '')
    contenido = utils_db.contenido
    
    if contenido is None or contenido.empty:
        await query.message.edit_text(
            "❌ No hay contenido cargado.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Menú principal", callback_data='menu')
            ]])
        )
        return
    
    filtered = contenido[contenido['genre'].str.contains(genre, na=False, case=False)]
    
    if filtered.empty:
        await query.message.edit_text(
            f"No encontré contenido de {genre} 😅\n"
            "Intenta con otro género.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver a géneros", callback_data='browse_genres')
            ]])
        )
        return
    
    sample_size = min(20, len(filtered))
    titles = filtered.sample(n=sample_size)
    
    keyboard = []
    for idx, row in titles.iterrows():
        title_text = f"{row['title']} ({row['year']}) {'🎬' if row['type'] == 'película' else '📺'}"
        if len(title_text) > 60:
            title_text = title_text[:57] + "..."
        keyboard.append([InlineKeyboardButton(
            title_text,
            callback_data=f'details_{idx}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔄 Ver más de este género", callback_data=f'genre_{genre}')])
    keyboard.append([InlineKeyboardButton("« Volver a géneros", callback_data='browse_genres')])
    keyboard.append([InlineKeyboardButton("🏠 Menú principal", callback_data='menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"🎭 **Género: {genre}**\n\n"
        f"📊 Encontré {len(filtered)} títulos. Aquí hay {sample_size}:\n"
        f"👇 Selecciona uno para ver detalles:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    idx = int(query.data.replace('details_', ''))
    contenido = utils_db.contenido
    
    if contenido is None:
        await query.message.edit_text("Error: No hay contenido cargado")
        return
        
    item = contenido.iloc[idx]
    emoji = "🎬" if item['type'] == 'película' else "📺"
    
    mensaje = f"{emoji} **{item['title']}** ({item['year']})\n\n"
    mensaje += f"🎯 **Disponible en:**\n"
    mensaje += f"➤ {item['platform']}\n\n"
    mensaje += f"⭐ Calificación: {item['rating']}/10\n"
    mensaje += f"🎭 Género: {item['genre']}"
    
    keyboard = [
        [InlineKeyboardButton("🔍 Ver similares", callback_data=f"similar_{idx}")],
        [InlineKeyboardButton("« Volver a la lista", callback_data='browse_genres')],
        [InlineKeyboardButton("🏠 Menú principal", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        mensaje,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    user_id = update.effective_user.id
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(item['title'])

async def show_similar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    idx = int(query.data.replace('similar_', ''))
    contenido = utils_db.contenido
    
    if contenido is None:
        await query.message.edit_text("Error: No hay contenido cargado")
        return
        
    item = contenido.iloc[idx]
    recomendaciones = recomendar_contenido(item['title'], top_n=15)
    
    if not recomendaciones:
        await query.answer("No encontré recomendaciones similares 😅", show_alert=True)
        return
    
    keyboard = []
    for rec in recomendaciones[:15]:
        try:
            rec_match = contenido[contenido['title'] == rec['title']]
            if rec_match.empty:
                continue
            rec_idx = rec_match.index[0]
            
            year = rec.get('year', 'N/A')
            emoji = '🎬' if rec.get('type') == 'película' else '📺'
            title_text = f"{rec['title']} ({year}) {emoji}"
            
            if len(title_text) > 60:
                title_text = title_text[:57] + "..."
            
            keyboard.append([InlineKeyboardButton(
                title_text,
                callback_data=f'details_{rec_idx}'
            )])
        except Exception as e:
            logging.error(f"Error procesando recomendación: {e}")
            continue
    
    if not keyboard:
        await query.answer("No pude procesar las recomendaciones 😅", show_alert=True)
        return
    
    keyboard.append([InlineKeyboardButton("« Volver", callback_data=f'details_{idx}')])
    keyboard.append([InlineKeyboardButton("🏠 Menú principal", callback_data='menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"🔍 **Similar a: {item['title']}**\n\n"
        f"Aquí hay {len(keyboard)-2} recomendaciones similares:\n"
        f"👇 Selecciona una para ver detalles:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# -------------------
# Modo Sorpréndeme
# -------------------
async def random_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    contenido = utils_db.contenido
    if contenido is None or contenido.empty:
        msg = "No hay contenido cargado. Intenta más tarde."
        if query:
            await query.message.reply_text(msg)
        else:
            await update.message.reply_text(msg)
        return
    
    random_item = contenido.sample(n=1).iloc[0]
    idx = contenido[contenido['title'] == random_item['title']].index[0]
    
    emoji = "🎬" if random_item['type'] == 'película' else "📺"
    
    mensaje = f"🎲 **Te recomiendo:**\n\n"
    mensaje += f"{emoji} **{random_item['title']}** ({random_item['year']})\n"
    mensaje += f"🎯 Plataforma: {random_item['platform']}\n"
    mensaje += f"⭐ Calificación: {random_item['rating']}/10\n"
    mensaje += f"🎭 Género: {random_item['genre']}\n\n"
    mensaje += f"📝 {random_item['overview'][:150]}...\n"
    
    keyboard = [
        [InlineKeyboardButton("📖 Ver detalles completos", callback_data=f'details_{idx}')],
        [InlineKeyboardButton("🎲 Otra recomendación", callback_data='random')],
        [InlineKeyboardButton("🏠 Menú principal", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.message.edit_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# -------------------
# Sistema de filtros
# -------------------
async def start_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🎬 Película", callback_data='filter_type_película')],
        [InlineKeyboardButton("📺 Serie", callback_data='filter_type_serie')],
        [InlineKeyboardButton("🎭 Cualquiera", callback_data='filter_type_all')],
        [InlineKeyboardButton("« Volver", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "¿Qué tipo de contenido buscas?",
        reply_markup=reply_markup
    )
    return CHOOSING_TYPE

async def filter_by_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    content_type = query.data.replace('filter_type_', '')
    context.user_data['filter_type'] = content_type
    
    keyboard = [
        [InlineKeyboardButton("Netflix", callback_data='filter_platform_Netflix')],
        [InlineKeyboardButton("Disney+", callback_data='filter_platform_Disney Plus')],
        [InlineKeyboardButton("Amazon Prime", callback_data='filter_platform_Amazon Prime Video')],
        [InlineKeyboardButton("HBO Max", callback_data='filter_platform_HBO Max')],
        [InlineKeyboardButton("Apple TV+", callback_data='filter_platform_Apple TV Plus')],
        [InlineKeyboardButton("Todas", callback_data='filter_platform_all')],
        [InlineKeyboardButton("« Volver", callback_data='filter')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "¿En qué plataforma quieres buscar?",
        reply_markup=reply_markup
    )
    return CHOOSING_PLATFORM

async def show_filtered_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    platform = query.data.replace('filter_platform_', '')
    content_type = context.user_data.get('filter_type', 'all')
    
    contenido = utils_db.contenido
    if contenido is None:
        await query.message.edit_text("Error: No hay contenido cargado")
        return
        
    filtered = contenido.copy()
    
    if content_type != 'all':
        filtered = filtered[filtered['type'] == content_type]
    
    if platform != 'all':
        filtered = filtered[filtered['platform'].str.contains(platform, na=False)]
    
    if filtered.empty:
        await query.message.edit_text(
            "No encontré resultados con esos filtros 😅\n"
            "Intenta con otros criterios.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Menú principal", callback_data='menu')
            ]])
        )
        return ConversationHandler.END
    
    results = filtered.sample(n=min(15, len(filtered)))
    
    keyboard = []
    for idx, row in results.iterrows():
        title_text = f"{row['title']} ({row['year']}) {'🎬' if row['type'] == 'película' else '📺'}"
        if len(title_text) > 60:
            title_text = title_text[:57] + "..."
        keyboard.append([InlineKeyboardButton(
            title_text,
            callback_data=f'details_{idx}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔄 Ver más", callback_data=f'filter_platform_{platform}')])
    keyboard.append([InlineKeyboardButton("🏠 Menú principal", callback_data='menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"🎯 **Encontré {len(filtered)} resultados**\n\n"
        f"Mostrando {len(results)} títulos:\n"
        f"👇 Selecciona uno para ver detalles:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# -------------------
# Historial
# -------------------
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    history = user_history.get(user_id, [])
    
    if not history:
        await query.message.edit_text(
            "📜 Aún no has buscado nada.\n"
            "¡Empieza a explorar contenido! 🍿",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Menú principal", callback_data='menu')
            ]])
        )
        return
    
    mensaje = "📜 **Tu historial de búsquedas:**\n\n"
    for item in history[-10:]:
        mensaje += f"• {item}\n"
    
    keyboard = [[InlineKeyboardButton("🏠 Menú principal", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

# -------------------
# Manejo de mensajes (Chat con IA)
# -------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    texto_lower = texto.lower()
    user_id = update.effective_user.id
    
    contenido = utils_db.contenido
    if contenido is None:
        await update.message.reply_text("Error: No hay contenido cargado")
        return
    
    if 'ai_conversation' not in context.user_data:
        context.user_data['ai_conversation'] = []
    
    palabras_conversacion = [
        'hola', 'hey', 'hi', 'hello', 'buenas', 'qué tal', 'que tal', 
        'buenos días', 'buenas tardes', 'buenas noches', 'saludos',
        'adiós', 'adios', 'bye', 'chao', 'hasta luego', 'nos vemos',
        'gracias', 'thanks', 'thx', 'como estas', 'cómo estás',
        'qué', 'que', 'como', 'cómo', 'cuál', 'cual',
        'recomienda', 'opinas', 'piensas', 'crees', 'dime',
        'por qué', 'porque', 'ayuda', 'help'
    ]
    
    es_conversacion = (
        any(palabra in texto_lower for palabra in palabras_conversacion) or
        '?' in texto or
        len(texto.split()) <= 3
    )
    
    if not es_conversacion and len(texto) > 2:
        matches = contenido[contenido['title'].str.lower().str.contains(texto_lower, na=False, case=False)]
        
        if not matches.empty:
            item = matches.iloc[0]
            idx = matches.index[0]
            
            if user_id not in user_history:
                user_history[user_id] = []
            user_history[user_id].append(item['title'])
            
            emoji = "🎬" if item['type'] == 'película' else "📺"
            mensaje = f"{emoji} **{item['title']}** ({item['year']})\n\n"
            mensaje += f"🎯 **Disponible en:**\n➤ {item['platform']}\n\n"
            mensaje += f"⭐ Calificación: {item['rating']}/10\n"
            mensaje += f"🎭 Género: {item['genre']}"
            
            if len(matches) > 1:
                mensaje += f"\n\n💡 *Encontré {len(matches)} resultados. Mostrando el primero.*"
            
            keyboard = [
                [InlineKeyboardButton("🔍 Ver similares", callback_data=f"similar_{idx}")],
                [InlineKeyboardButton("🎬 Buscar contenido", callback_data='browse_genres')],
                [InlineKeyboardButton("🏠 Menú principal", callback_data='menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')
            return
    
    ai_response = chat_with_ai(texto, context.user_data['ai_conversation'])
    
    context.user_data['ai_conversation'].append({"role": "user", "content": texto})
    context.user_data['ai_conversation'].append({"role": "assistant", "content": ai_response})
    
    if len(context.user_data['ai_conversation']) > 20:
        context.user_data['ai_conversation'] = context.user_data['ai_conversation'][-20:]
    
    keyboard = [
        [InlineKeyboardButton("🎬 Buscar por géneros", callback_data='browse_genres')],
        [InlineKeyboardButton("🎲 Sorpréndeme", callback_data='random')],
        [InlineKeyboardButton("🏠 Menú principal", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(ai_response, reply_markup=reply_markup)

# -------------------
# Callbacks
# -------------------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query.data == 'menu':
        await query.answer()
        keyboard = [
            [InlineKeyboardButton("🎬 Buscar contenido", callback_data='browse_genres')],
            [InlineKeyboardButton("🎲 Sorpréndeme", callback_data='random')],
            [InlineKeyboardButton("📊 Filtrar por criterios", callback_data='filter')],
            [InlineKeyboardButton("📜 Mi historial", callback_data='history')],
            [InlineKeyboardButton("❓ Ayuda", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("¿Qué te gustaría hacer?", reply_markup=reply_markup)
    
    elif query.data == 'browse_genres':
        await browse_genres(update, context)
    
    elif query.data.startswith('genre_'):
        await show_titles_by_genre(update, context)
    
    elif query.data.startswith('details_'):
        await show_details(update, context)
    
    elif query.data.startswith('similar_'):
        await show_similar(update, context)
    
    elif query.data == 'random':
        await random_recommendation(update, context)
    
    elif query.data == 'filter':
        await start_filter(update, context)
    
    elif query.data == 'history':
        await show_history(update, context)
    
    elif query.data == 'help':
        await help_command(update, context)
    
    elif query.data.startswith('like_'):
        title = query.data.replace('like_', '')
        await query.answer(f"¡Genial! Me alegra que te guste {title} 👍")

# -------------------
# Main
# -------------------
if __name__ == "__main__":
    cargar_contenido("movies_clean.csv")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    filter_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_filter, pattern='^filter$')],
        states={
            CHOOSING_TYPE: [CallbackQueryHandler(filter_by_type, pattern='^filter_type_')],
            CHOOSING_PLATFORM: [CallbackQueryHandler(show_filtered_results, pattern='^filter_platform_')]
        },
        fallbacks=[CallbackQueryHandler(button_callback, pattern='^menu$')]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("random", random_recommendation))
    app.add_handler(filter_handler)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot CineClass iniciado correctamente. Esperando mensajes...")
    app.run_polling()
