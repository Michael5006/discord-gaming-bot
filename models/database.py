import aiosqlite
import os
from datetime import datetime

DATABASE_PATH = 'data/games.db'

async def init_db():
    """Inicializa la base de datos y crea las tablas necesarias"""
    
    # Crear carpeta data si no existe
    os.makedirs('data', exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Tabla de usuarios
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                total_points INTEGER DEFAULT 0,
                total_games INTEGER DEFAULT 0,
                is_elkie INTEGER DEFAULT 0,
                join_date TEXT NOT NULL,
                role TEXT DEFAULT 'NORMAL'
            )
        ''')
        
        # Tabla de juegos
        await db.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                game_name TEXT NOT NULL,
                category TEXT NOT NULL,
                platform TEXT NOT NULL,
                has_platinum INTEGER DEFAULT 0,
                is_recompleted INTEGER DEFAULT 0,
                total_points INTEGER NOT NULL,
                status TEXT DEFAULT 'PENDING',
                evidence_url TEXT,
                submission_date TEXT NOT NULL,
                reviewed_by INTEGER,
                review_date TEXT,
                rejection_reason TEXT,
                FOREIGN KEY (discord_user_id) REFERENCES users (discord_id)
            )
        ''')
        
        # Tabla de lista negra
        await db.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_name TEXT NOT NULL UNIQUE,
                reason TEXT NOT NULL,
                added_by INTEGER NOT NULL,
                added_date TEXT NOT NULL
            )
        ''')
        
        await db.commit()
        print('✅ Base de datos inicializada correctamente')

async def get_db():
    """Retorna una conexión a la base de datos"""
    return await aiosqlite.connect(DATABASE_PATH)