import requests
import config
from typing import List, Dict, Optional

class RAWGClient:
    """Cliente para interactuar con la API de RAWG"""
    
    def __init__(self):
        self.api_key = config.RAWG_API_KEY
        self.base_url = config.RAWG_BASE_URL
        self.cache = {}  # Caché simple para búsquedas
        
        # Publishers considerados AAA
        self.aaa_publishers = [
            'sony', 'playstation', 'sie', 'microsoft', 'xbox', 'nintendo',
            'ubisoft', 'electronic arts', 'ea', 'ea games',
            'activision', 'blizzard', 'activision blizzard',
            'square enix', 'capcom', 'bandai namco', 'namco',
            'sega', 'rockstar', 'rockstar games', 'take-two', '2k games',
            'bethesda', 'zenimax', 'warner bros', 'wb games',
            'thq nordic', 'embracer', 'konami', 'atlus'
        ]
        
        # Publishers considerados Indie
        self.indie_publishers = [
            'devolver digital', 'annapurna', 'team17', 'raw fury',
            'humble games', 'coffee stain', 'panic', 'finji'
        ]
    
    def search_games(self, query: str, limit: int = 25) -> List[Dict]:
        """Busca juegos por nombre"""
        
        # Verificar caché
        cache_key = f"search_{query.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            params = {
                'key': self.api_key,
                'search': query,
                'page_size': limit,
                'platforms': '187,4,18',  # PS5=187, PC=4, PS4=18
                'exclude_additions': 'true',  # Excluir DLCs
                'ordering': '-added,-rating'  # Por popularidad y rating
            }
            
            response = requests.get(
                f'{self.base_url}/games',
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                # Filtrar y formatear resultados
                formatted_results = []
                seen_names = set()  # Para evitar duplicados
                
                for game in results:
                    formatted_game = self._format_game(game)
                    if formatted_game:
                        # Evitar duplicados por nombre + año
                        game_key = f"{formatted_game['name'].lower()}_{formatted_game['year']}"
                        
                        # Solo agregar si no está duplicado y tiene año válido
                        if game_key not in seen_names and formatted_game['year'] != 'Unknown':
                            seen_names.add(game_key)
                            formatted_results.append(formatted_game)
                
                # Guardar en caché
                self.cache[cache_key] = formatted_results
                
                # Ordenar por score combinado (popularidad + calidad)
                def get_score(game):
                    added = game.get('added', 0)
                    metacritic = game.get('metacritic', 0)
                    
                    # Score = 70% popularidad + 30% metacritic
                    popularity_score = added / 1000  # Normalizar
                    quality_score = metacritic * 100 if metacritic else 0
                    
                    return popularity_score + quality_score
                
                formatted_results.sort(key=get_score, reverse=True)
                
                return formatted_results
            
            return []
            
        except Exception as e:
            print(f'Error buscando juegos en RAWG: {e}')
            return []
    
    def get_game_details(self, game_id: int) -> Optional[Dict]:
        """Obtiene detalles completos de un juego"""
        
        try:
            params = {'key': self.api_key}
            
            response = requests.get(
                f'{self.base_url}/games/{game_id}',
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            print(f'Error obteniendo detalles del juego: {e}')
            return None
    
    def _format_game(self, game: Dict) -> Optional[Dict]:
        """Formatea la información del juego"""
        
        try:
            # Información básica
            game_id = game.get('id')
            name = game.get('name', 'Unknown')
            released = game.get('released', '')
            year = released.split('-')[0] if released else 'Unknown'
            
            # Plataformas
            platforms_data = game.get('platforms', [])
            platforms = []
            has_ps5 = False
            has_steam = False
            
            for p in platforms_data:
                platform_info = p.get('platform', {})
                platform_name = platform_info.get('name', '')
                
                if 'PlayStation 5' in platform_name:
                    platforms.append('PS5')
                    has_ps5 = True
                elif 'PC' in platform_name:
                    platforms.append('Steam')
                    has_steam = True
                elif 'PlayStation 4' in platform_name and not has_ps5:
                    platforms.append('PS4')
            
            # Solo incluir si tiene PS5 o Steam
            if not (has_ps5 or has_steam):
                return None
            
            # Metacritic
            metacritic = game.get('metacritic', 0)
            
            # Popularidad
            added = game.get('added', 0)
            
            # Imagen
            background_image = game.get('background_image', '')
            
            # Detectar categoría
            category = self._detect_category(game, year, metacritic)
            
            return {
                'id': game_id,
                'name': name,
                'year': year,
                'platforms': platforms,
                'category': category,
                'metacritic': metacritic,
                'added': added,  # <- NUEVO
                'image': background_image
            }
            
        except Exception as e:
            print(f'Error formateando juego: {e}')
            return None
    
    def _detect_category(self, game: Dict, year: str, metacritic: int) -> str:
        """Detecta la categoría del juego (Retro/Indie/AA/AAA)"""
        
        try:
            # RETRO: Juegos hasta 2005 (6ta generación)
            if year.isdigit() and int(year) <= 2005:
                return 'Retro'
            
            # Obtener información
            game_name_lower = game.get('name', '').lower()
            
            publishers = game.get('publishers', [])
            publisher_names = [p.get('name', '').lower() for p in publishers]
            
            developers = game.get('developers', [])
            developer_names = [d.get('name', '').lower() for d in developers]
            
            tags = game.get('tags', [])
            tag_names = [t.get('name', '').lower() for t in tags]
            
            # Obtener rating (cantidad de reviews)
            ratings_count = game.get('ratings_count', 0)
            added = game.get('added', 0)  # Cuánta gente lo agregó
            
            # FRANCHISES AAA CONOCIDAS (esto es clave)
            aaa_franchises = [
                'god of war', 'halo', 'gears of war', 'uncharted', 'the last of us',
                'horizon', 'ghost of tsushima', 'spider-man', 'spiderman',
                'call of duty', 'battlefield', 'assassin', 'far cry', 'watch dogs',
                'grand theft auto', 'gta', 'red dead', 'elder scrolls', 'fallout',
                'doom', 'wolfenstein', 'resident evil', 'final fantasy', 'dragon quest',
                'metal gear', 'death stranding', 'cyberpunk', 'witcher',
                'fifa', 'madden', 'nba 2k', 'forza', 'gran turismo',
                'tomb raider', 'hitman', 'deus ex', 'borderlands', 'bioshock',
                'mass effect', 'dragon age', 'destiny', 'overwatch', 'diablo',
                'world of warcraft', 'starcraft', 'minecraft', 'fortnite',
                'league of legends', 'valorant', 'apex legends', 'titanfall',
                'dark souls', 'elden ring', 'bloodborne', 'sekiro',
                'monster hunter', 'street fighter', 'mortal kombat', 'tekken',
                'persona', 'yakuza', 'judgment', 'kingdom hearts',
                'batman arkham', 'mortal kombat', 'injustice', 'lego'
            ]
            
            # Verificar si es una franchise AAA
            is_aaa_franchise = False
            for franchise in aaa_franchises:
                if franchise in game_name_lower:
                    is_aaa_franchise = True
                    break
            
            # INDIE: Tags o publishers indie (pero no si es franchise AAA)
            if not is_aaa_franchise:
                if 'indie' in tag_names:
                    if ratings_count < 100000:
                        return 'Indie'
                
                for pub in publisher_names:
                    for indie_pub in self.indie_publishers:
                        if indie_pub in pub:
                            return 'Indie'
            
            # AAA: Múltiples criterios
            is_aaa = False
            
            # 1. Franchise AAA conocida
            if is_aaa_franchise:
                is_aaa = True
            
            # 2. Publisher AAA
            for pub in publisher_names:
                for aaa_pub in self.aaa_publishers:
                    if aaa_pub in pub:
                        is_aaa = True
                        break
            
            # 3. Developer AAA
            aaa_developers = [
                'santa monica', 'naughty dog', 'insomniac', 'guerrilla',
                'sucker punch', 'polyphony', 'kojima productions',
                'bungie', 'id software', 'dice', 'respawn', 'infinity ward',
                'treyarch', 'sledgehammer', 'from software', 'cd projekt',
                'bethesda game studios', 'bioware', 'rocksteady', 'remedy'
            ]
            
            for dev in developer_names:
                for aaa_dev in aaa_developers:
                    if aaa_dev in dev:
                        is_aaa = True
                        break
            
            # 4. Metacritic alto Y popularidad
            if metacritic and metacritic >= 75 and added > 30000:
                is_aaa = True
            
            # 5. Muy popular (más de 100k personas lo agregaron)
            if added > 100000:
                is_aaa = True
            
            if is_aaa:
                return 'Aaa'
            
            # AA: Metacritic medio-alto o popularidad media
            if metacritic and metacritic >= 70:
                return 'Aa'
            
            if added > 20000:
                return 'Aa'
            
            # Por defecto: AA
            return 'Aa'
            
        except Exception as e:
            print(f'Error detectando categoría: {e}')
            return 'Aa'
    
    def has_platform(self, game_platforms: List[str], target_platform: str) -> bool:
        """Verifica si un juego está disponible en la plataforma especificada"""
        
        if target_platform == 'PS5':
            return 'PS5' in game_platforms or 'PS4' in game_platforms
        elif target_platform == 'Steam':
            return 'Steam' in game_platforms
        
        return False

# Instancia global del cliente
rawg_client = RAWGClient()