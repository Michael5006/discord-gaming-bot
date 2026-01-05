import aiosqlite
import os

DATABASE_PATH = 'data/games.db'

async def get_db():
    """Retorna una conexión a la base de datos"""
    return await aiosqlite.connect(DATABASE_PATH)


async def init_db():
    """Inicializa la base de datos y crea las tablas necesarias"""
    
    # Crear carpeta data si no existe
    os.makedirs('data', exist_ok=True)
    
    db = await get_db()
    
    try:
        # Tabla de usuarios
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                total_points INTEGER DEFAULT 0,
                total_games INTEGER DEFAULT 0,
                is_elkie INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de juegos (usando submission_date en lugar de created_at)
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
                submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                rejection_reason TEXT,
                image_url TEXT DEFAULT ''
            )
        ''')
        
        await db.commit()
        
        print('✅ Base de datos inicializada correctamente')
        
        # Verificar esquema
        await fix_database_schema()
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
    finally:
        await db.close()


async def fix_database_schema():
    """Verifica y corrige el esquema de la BD agregando columnas faltantes"""
    try:
        db = await get_db()
        
        # Obtener columnas actuales
        cursor = await db.execute("PRAGMA table_info(games)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Columnas actuales en 'games': {', '.join(column_names)}")
        
        cambios = False
        
        # Agregar image_url si falta
        if 'image_url' not in column_names:
            print("⚙️ Agregando columna 'image_url'...")
            await db.execute("ALTER TABLE games ADD COLUMN image_url TEXT DEFAULT ''")
            cambios = True
            print("✅ Columna 'image_url' agregada")
        
        if cambios:
            await db.commit()
            print("✅ Esquema de BD actualizado")
        else:
            print("✅ Esquema de BD está correcto")
        
        await db.close()
        
    except Exception as e:
        print(f"⚠️ Error verificando esquema: {e}")