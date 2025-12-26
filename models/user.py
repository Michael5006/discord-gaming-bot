from datetime import datetime
from models.database import get_db

class User:
    """Modelo para manejar usuarios del concurso"""
    
    def __init__(self, discord_id, username, total_points=0, total_games=0, 
                 is_elkie=False, join_date=None, role='NORMAL'):
        self.discord_id = discord_id
        self.username = username
        self.total_points = total_points
        self.total_games = total_games
        self.is_elkie = is_elkie
        self.join_date = join_date or datetime.now().isoformat()
        self.role = role
    
    @staticmethod
    async def create(discord_id, username):
        """Crea un nuevo usuario en la base de datos"""
        db = await get_db()
        try:
            await db.execute('''
                INSERT INTO users (discord_id, username, join_date)
                VALUES (?, ?, ?)
            ''', (discord_id, username, datetime.now().isoformat()))
            await db.commit()
            return True
        except Exception as e:
            print(f'Error al crear usuario: {e}')
            return False
        finally:
            await db.close()
    
    @staticmethod
    async def get(discord_id):
        """Obtiene un usuario por su Discord ID"""
        db = await get_db()
        try:
            async with db.execute('''
                SELECT * FROM users WHERE discord_id = ?
            ''', (discord_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        discord_id=row[0],
                        username=row[1],
                        total_points=row[2],
                        total_games=row[3],
                        is_elkie=bool(row[4]),
                        join_date=row[5],
                        role=row[6]
                    )
                return None
        finally:
            await db.close()
    
    @staticmethod
    async def get_or_create(discord_id, username):
        """Obtiene un usuario o lo crea si no existe"""
        user = await User.get(discord_id)
        if not user:
            await User.create(discord_id, username)
            user = await User.get(discord_id)
        return user
    
    @staticmethod
    async def update_stats(discord_id):
        """Actualiza las estadísticas del usuario (puntos y juegos totales)"""
        db = await get_db()
        try:
            # Calcular puntos totales de juegos aprobados
            async with db.execute('''
                SELECT COUNT(*), COALESCE(SUM(total_points), 0)
                FROM games
                WHERE discord_user_id = ? AND status = 'APPROVED'
            ''', (discord_id,)) as cursor:
                row = await cursor.fetchone()
                total_games = row[0]
                total_points = row[1]
            
            # Actualizar usuario
            await db.execute('''
                UPDATE users
                SET total_points = ?, total_games = ?
                WHERE discord_id = ?
            ''', (total_points, total_games, discord_id))
            
            await db.commit()
            return True
        except Exception as e:
            print(f'Error al actualizar stats: {e}')
            return False
        finally:
            await db.close()
    
    @staticmethod
    async def get_all_ranked():
        """Obtiene todos los usuarios ordenados por puntos (ranking)"""
        db = await get_db()
        try:
            users = []
            async with db.execute('''
                SELECT * FROM users
                ORDER BY total_points DESC, total_games DESC
            ''') as cursor:
                async for row in cursor:
                    users.append(User(
                        discord_id=row[0],
                        username=row[1],
                        total_points=row[2],
                        total_games=row[3],
                        is_elkie=bool(row[4]),
                        join_date=row[5],
                        role=row[6]
                    ))
            return users
        finally:
            await db.close()