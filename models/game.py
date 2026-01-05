from datetime import datetime
from models.database import get_db
import config

class Game:
    """Modelo para manejar juegos registrados"""
    
    def __init__(self, id, discord_user_id, username, game_name, category,
                 platform, has_platinum, is_recompleted, total_points, 
                 status, created_at, reviewed_by, reviewed_at, rejection_reason,
                 image_url=''):
        self.id = id
        self.discord_user_id = discord_user_id
        self.username = username
        self.game_name = game_name
        self.category = category
        self.platform = platform
        self.has_platinum = has_platinum
        self.is_recompleted = is_recompleted
        self.total_points = total_points
        self.status = status
        self.created_at = created_at
        self.reviewed_by = reviewed_by
        self.reviewed_at = reviewed_at
        self.rejection_reason = rejection_reason
        self.image_url = image_url
    
    @staticmethod
    async def create(discord_user_id: int, username: str, game_name: str, 
                    category: str, platform: str, has_platinum: bool, 
                    is_recompleted: bool, image_url: str = '') -> bool:
        """Crea un nuevo juego"""
        try:
            from models.database import get_db
            
            # Calcular puntos
            points = config.PUNTOS_CATEGORIA[category.lower()]
            if has_platinum:
                points += config.PUNTOS_CATEGORIA['platino']
            
            db = await get_db()
            
            # Usar solo created_at (no submission_date)
            await db.execute('''
                INSERT INTO games (
                    discord_user_id, username, game_name, category, 
                    platform, has_platinum, is_recompleted, total_points,
                    status, image_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
            ''', (discord_user_id, username, game_name, category, 
                  platform, int(has_platinum), int(is_recompleted), 
                  points, image_url))
            
            await db.commit()
            await db.close()
            return True
            
        except Exception as e:
            print(f'Error creando juego: {e}')
            return False
    
    @staticmethod
    async def get_pending() -> list:
        """Obtiene todos los juegos pendientes"""
        try:
            db = await get_db()
            cursor = await db.execute('''
                SELECT id, discord_user_id, username, game_name, category,
                       platform, has_platinum, is_recompleted, total_points,
                       status, created_at, reviewed_by, reviewed_at, 
                       rejection_reason, image_url
                FROM games
                WHERE status = 'PENDING'
                ORDER BY created_at ASC
            ''')
            
            rows = await cursor.fetchall()
            await db.close()
            
            games = []
            for row in rows:
                games.append(Game(*row))
            
            return games
        except Exception as e:
            print(f'Error obteniendo juegos pendientes: {e}')
            return []
    
    @staticmethod
    async def get_by_user(discord_user_id: int, status: str = None) -> list:
        """Obtiene todos los juegos de un usuario"""
        try:
            db = await get_db()
            
            if status:
                cursor = await db.execute('''
                    SELECT id, discord_user_id, username, game_name, category,
                           platform, has_platinum, is_recompleted, total_points,
                           status, created_at, reviewed_by, reviewed_at, 
                           rejection_reason, image_url
                    FROM games
                    WHERE discord_user_id = ? AND status = ?
                    ORDER BY created_at DESC
                ''', (discord_user_id, status))
            else:
                cursor = await db.execute('''
                    SELECT id, discord_user_id, username, game_name, category,
                           platform, has_platinum, is_recompleted, total_points,
                           status, created_at, reviewed_by, reviewed_at, 
                           rejection_reason, image_url
                    FROM games
                    WHERE discord_user_id = ?
                    ORDER BY created_at DESC
                ''', (discord_user_id,))
            
            rows = await cursor.fetchall()
            await db.close()
            
            games = []
            for row in rows:
                games.append(Game(*row))
            
            return games
        except Exception as e:
            print(f'Error obteniendo juegos del usuario: {e}')
            return []
    
    @staticmethod
    async def get_by_id(game_id: int):
        """Obtiene un juego por ID"""
        try:
            db = await get_db()
            cursor = await db.execute('''
                SELECT id, discord_user_id, username, game_name, category,
                       platform, has_platinum, is_recompleted, total_points,
                       status, created_at, reviewed_by, reviewed_at, 
                       rejection_reason, image_url
                FROM games
                WHERE id = ?
            ''', (game_id,))
            
            row = await cursor.fetchone()
            await db.close()
            
            if row:
                return Game(*row)
            return None
        except Exception as e:
            print(f'Error obteniendo juego: {e}')
            return None
    
    @staticmethod
    async def approve(game_id, admin_id):
        """Aprueba un juego"""
        db = await get_db()
        try:
            await db.execute('''
                UPDATE games
                SET status = 'APPROVED',
                    reviewed_by = ?,
                    review_date = ?
                WHERE id = ?
            ''', (admin_id, datetime.now().isoformat(), game_id))
            await db.commit()
            return True
        except Exception as e:
            print(f'Error al aprobar juego: {e}')
            return False
        finally:
            await db.close()
    
    @staticmethod
    async def reject(game_id, admin_id, reason):
        """Rechaza un juego"""
        db = await get_db()
        try:
            await db.execute('''
                UPDATE games
                SET status = 'REJECTED',
                    reviewed_by = ?,
                    review_date = ?,
                    rejection_reason = ?
                WHERE id = ?
            ''', (admin_id, datetime.now().isoformat(), reason, game_id))
            await db.commit()
            return True
        except Exception as e:
            print(f'Error al rechazar juego: {e}')
            return False
        finally:
            await db.close()