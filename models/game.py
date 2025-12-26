from datetime import datetime
from models.database import get_db
import config

class Game:
    """Modelo para manejar juegos registrados"""
    
    def __init__(self, id, discord_user_id, username, game_name, category, 
                 platform, has_platinum, is_recompleted, total_points, status,
                 evidence_url=None, submission_date=None, reviewed_by=None,
                 review_date=None, rejection_reason=None):
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
        self.evidence_url = evidence_url
        self.submission_date = submission_date or datetime.now().isoformat()
        self.reviewed_by = reviewed_by
        self.review_date = review_date
        self.rejection_reason = rejection_reason
    
    @staticmethod
    async def create(discord_user_id, username, game_name, category, platform, 
                     has_platinum=False, is_recompleted=False, evidence_url=None):
        """Crea un nuevo registro de juego"""
        db = await get_db()
        try:
            # Calcular puntos
            points = config.PUNTOS_CATEGORIA[category.lower()]
            if has_platinum:
                points += config.PUNTOS_CATEGORIA['platino']
            
            await db.execute('''
                INSERT INTO games (
                    discord_user_id, username, game_name, category, 
                    platform, has_platinum, is_recompleted, total_points,
                    status, evidence_url, submission_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)
            ''', (discord_user_id, username, game_name, category, platform,
                  int(has_platinum), int(is_recompleted), points, 
                  evidence_url, datetime.now().isoformat()))
            
            await db.commit()
            return True
        except Exception as e:
            print(f'Error al crear juego: {e}')
            return False
        finally:
            await db.close()
    
    @staticmethod
    async def get_pending():
        """Obtiene todos los juegos pendientes de aprobación"""
        db = await get_db()
        try:
            games = []
            async with db.execute('''
                SELECT * FROM games WHERE status = 'PENDING'
                ORDER BY submission_date ASC
            ''') as cursor:
                async for row in cursor:
                    games.append(Game(*row))
            return games
        finally:
            await db.close()
    
    @staticmethod
    async def get_by_user(discord_user_id, status=None):
        """Obtiene juegos de un usuario específico"""
        db = await get_db()
        try:
            games = []
            if status:
                query = 'SELECT * FROM games WHERE discord_user_id = ? AND status = ? ORDER BY submission_date DESC'
                params = (discord_user_id, status)
            else:
                query = 'SELECT * FROM games WHERE discord_user_id = ? ORDER BY submission_date DESC'
                params = (discord_user_id,)
            
            async with db.execute(query, params) as cursor:
                async for row in cursor:
                    games.append(Game(*row))
            return games
        finally:
            await db.close()
    
    @staticmethod
    async def get_by_id(game_id):
        """Obtiene un juego por su ID"""
        db = await get_db()
        try:
            async with db.execute('''
                SELECT * FROM games WHERE id = ?
            ''', (game_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Game(*row)
                return None
        finally:
            await db.close()
    
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