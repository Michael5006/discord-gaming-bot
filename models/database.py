import aiosqlite
import os

DATABASE_PATH = 'data/games.db'

async def debug_schema():
    """Muestra el esquema completo de la BD"""
    try:
        db = await get_db()
        
        print("\n" + "="*60)
        print("🔍 DEBUG: ESTRUCTURA DE LA BASE DE DATOS")
        print("="*60)
        
        # Ver estructura de tabla games
        cursor = await db.execute("PRAGMA table_info(games)")
        columns = await cursor.fetchall()
        
        print("\n📋 TABLA 'games':")
        print("-" * 60)
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            print(f"  {col_id}. {name:20} {type_:15} NULL={not notnull} DEFAULT={default} PK={pk}")
        
        print("\n" + "="*60 + "\n")
        
        await db.close()
        
    except Exception as e:
        print(f"❌ Error en debug_schema: {e}")

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
                submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                rejection_reason TEXT,
                image_url TEXT DEFAULT ''
            )
        ''')
        
        await db.commit()
        
        print('✅ Base de datos inicializada correctamente')
        
        # DEBUG: Mostrar estructura real
        await debug_schema()
        
        # Verificar esquema
        await fix_database_schema()
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
    finally:
        await db.close()


async def fix_database_schema():
    """Verifica que el esquema esté correcto"""
    try:
        db = await get_db()
        
        cursor = await db.execute("PRAGMA table_info(games)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Columnas actuales en 'games': {', '.join(column_names)}")
        print("✅ Esquema de BD está correcto")
        
        await db.close()
        
    except Exception as e:
        print(f"⚠️ Error verificando esquema: {e}")