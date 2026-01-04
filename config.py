import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Token del bot
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

# API de RAWG para búsqueda de juegos
RAWG_API_KEY = os.getenv('RAWG_API_KEY')
RAWG_BASE_URL = 'https://api.rawg.io/api'

# Configuración del concurso
CONTEST_START_DATE = datetime.strptime(os.getenv('CONTEST_START_DATE', '2025-12-25'), '%Y-%m-%d')
CONTEST_END_DATE = datetime.strptime(os.getenv('CONTEST_END_DATE', '2027-01-01'), '%Y-%m-%d')

# Colores para embeds (en hexadecimal)
COLORES = {
    'retro': 0x3498db,      # Azul
    'indie': 0x2ecc71,      # Verde
    'aa': 0xf39c12,         # Naranja
    'aaa': 0xe74c3c,        # Rojo
    'platino': 0x9b59b6,    # Morado
    'aprobado': 0x2ecc71,   # Verde
    'pendiente': 0xf39c12,  # Naranja
    'rechazado': 0xe74c3c,  # Rojo
    'info': 0x3498db        # Azul
}

# Emojis consistentes
EMOJIS = {
    # Acciones
    'registrar': '🎮',
    'aprobar': '✅',
    'rechazar': '❌',
    'pendiente': '⏳',
    'editar': '✏️',
    'eliminar': '🗑️',
    
    # Categorías
    'retro': '🕹️',
    'indie': '🎨',
    'aa': '🎯',
    'aaa': '👑',
    'platino': '🏆',
    
    # Plataformas
    'ps5': '🎮',
    'steam': '💻',
    
    # Stats
    'puntos': '💰',
    'ranking': '📊',
    'usuario': '👤',
    'fecha': '📅',
    'tiempo': '⏰',
    
    # Otros
    'advertencia': '⚠️',
    'info': 'ℹ️',
    'exito': '🎉',
    'error': '❌',
    'buscar': '🔍',
    'config': '⚙️',
}

# Puntuación por categoría
PUNTOS_CATEGORIA = {
    'retro': 1,
    'indie': 1,
    'aa': 2,
    'aaa': 3,
    'platino': 1  # Bonus adicional
}

# Plataformas válidas
PLATAFORMAS = ['PS5', 'Steam']

# Categorías de juegos
CATEGORIAS = ['Retro', 'Indie', 'AA', 'AAA']