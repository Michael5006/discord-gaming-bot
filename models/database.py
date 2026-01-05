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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_by INTEGER,
                    reviewed_at TIMESTAMP,
                    rejection_reason TEXT,
                    image_url TEXT
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
        
async def init_db():
    """Inicializa la base de datos"""
    db = await get_db()
    
    try:
        # Crear tabla de usuarios
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                total_points INTEGER DEFAULT 0,
                total_games INTEGER DEFAULT 0,
                is_elkie INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear tabla de juegos
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                rejection_reason TEXT,
                image_url TEXT
            )
        ''')
        
        await db.commit()
        
        # Ejecutar migración para agregar image_url si no existe
        await migrate_add_image_url()
        
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"Error inicializando base de datos: {e}")
    finally:
        await db.close()
        
        await db.commit()
        print('✅ Base de datos inicializada correctamente')

async def get_db():
    """Retorna una conexión a la base de datos"""
    return await aiosqlite.connect(DATABASE_PATH)

async def migrate_add_image_url():
    """Migración: Agregar columna image_url a la tabla games"""
    try:
        db = await get_db()
        
        # Verificar si la columna ya existe
        cursor = await db.execute("PRAGMA table_info(games)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'image_url' not in column_names:
            print("Agregando columna image_url...")
            await db.execute('''
                ALTER TABLE games ADD COLUMN image_url TEXT DEFAULT ''
            ''')
            await db.commit()
            print("✅ Columna image_url agregada exitosamente")
        else:
            print("✅ Columna image_url ya existe")
        
        await db.close()
    except Exception as e:
        print(f"Error en migración: {e}")