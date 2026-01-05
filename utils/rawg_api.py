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
            'humble games', 'coffee stain', 'panic', 'finji', 'stunlock studios'
        ]
        
        # Franquicias AAA (Para asegurar que juegos como "RE4 Remake" sean AAA)
        self.aaa_franchises = [
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
                'batman arkham', 'injustice', 'lego'
        ]
    
    def search_games(self, query: str, limit: int = 25) -> List[Dict]:
        """Busca juegos por nombre con agrupación inteligente"""
        
        # Verificar caché
        cache_key = f"search_{query.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Buscar SIN filtro de plataformas
            params = {
                'key': self.api_key,
                'search': query,
                'page_size': 40,
                'exclude_additions': 'false'
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
                seen_ids = set()
                
                for game in results:
                    game_id = game.get('id')
                    if game_id in seen_ids:
                        continue
                    
                    formatted_game = self._format_game(game)
                    if formatted_game and formatted_game['year'] != 'Unknown':
                        seen_ids.add(game_id)
                        formatted_results.append(formatted_game)
                
                # PASO 1: Agrupar por nombre base
                groups = {}
                for game in formatted_results:
                    base_name = self._get_base_name(game['name'])
                    if base_name not in groups:
                        groups[base_name] = []
                    groups[base_name].append(game)
                
                # PASO 2: Calcular score de cada grupo
                query_normalized = self._normalize_text(query)
                group_scores = []
                
                for base_name, games_in_group in groups.items():
                    # Score del grupo basado en coincidencia con búsqueda
                    group_match_score = self._get_group_match_score(query_normalized, base_name, games_in_group)
                    
                    # Ordenar juegos DENTRO del grupo (más reciente primero)
                    games_in_group.sort(key=lambda g: (
                        int(g['year']) if g['year'].isdigit() else 0,
                        g.get('added', 0)
                    ), reverse=True)
                    
                    group_scores.append({
                        'base_name': base_name,
                        'games': games_in_group,
                        'score': group_match_score
                    })
                
                # PASO 3: Ordenar grupos por score
                group_scores.sort(key=lambda x: x['score'], reverse=True)
                
                # PASO 4: Aplanar grupos de vuelta a lista
                final_results = []
                for group in group_scores:
                    final_results.extend(group['games'])
                
                # Limitar resultados
                final_results = final_results[:limit]
                
                # Guardar en caché
                self.cache[cache_key] = final_results
                
                return final_results
            
            return []
            
        except Exception as e:
            print(f'Error buscando juegos en RAWG: {e}')
            return []
    
    def _get_base_name(self, name: str) -> str:
        """Extrae el nombre base del juego (sin año, remake, etc.)"""
        base = name.lower()
        
        # Remover sufijos comunes
        suffixes_to_remove = [
            'game of the year', 'goty', 'complete edition', 'deluxe',
            'ultimate edition', 'enhanced edition', 'special edition',
            'directors cut', "director's cut", 'gold edition'
        ]
        
        for suffix in suffixes_to_remove:
            base = base.replace(suffix, '')
        
        # Remover años entre paréntesis: (2023), (2005)
        import re
        base = re.sub(r'\(\d{4}\)', '', base)
        
        # Remover símbolos y espacios extras
        base = base.replace('™', '').replace('®', '').replace(':', '').strip()
        base = re.sub(r'\s+', ' ', base)  # Múltiples espacios a uno solo
        
        return base
    
    def _get_group_match_score(self, query: str, base_name: str, games: List[Dict]) -> int:
        """Calcula el score de un grupo de juegos"""
        
        # Score base: popularidad del juego más popular del grupo
        max_added = max((game.get('added') or 0) for game in games)
        max_metacritic = max((game.get('metacritic') or 0) for game in games)
        
        score = max_added * 0.5
        
        #Busqueda Exacta
        if query.lower() in base_name.lower():
            score += 100000
        
        #Normalizar meta
        if max_metacritic is None:
            max_metacritic = 0
        
        # Bonus por metacritic alto
        if max_metacritic >= 90:
            score += 50000
        elif max_metacritic >= 80:
            score += 30000
        elif max_metacritic >= 70:
            score += 10000
        
        # BONUS MASIVO por coincidencia exacta o muy cercana
        query_words = set(query.split())
        base_words = set(base_name.split())
        
        if not query_words:
            return score
        
        # Coincidencia perfecta
        if query == base_name:
            score += 500000  # MEGA BONUS
        # Coincidencia muy alta (>= 80%)
        elif query_words.issubset(base_words) or base_words.issubset(query_words):
            score += 300000
        else:
            # Coincidencia parcial
            common = query_words.intersection(base_words)
            similarity = len(common) / len(query_words)
            
            if similarity >= 0.8:
                score += 200000
            elif similarity >= 0.6:
                score += 100000
            elif similarity >= 0.4:
                score += 50000
        
        # Bonus si es franchise AAA conocida
        aaa_terms = [
            'resident evil', 'the last of us', 'god of war', 
            'uncharted', 'halo', 'grand theft auto', 'red dead',
            'call of duty', 'assassin', 'final fantasy'
        ]
        
        for term in aaa_terms:
            if term in base_name:
                score += 30000
                break
        
        # Bonus por juegos recientes en el grupo
        has_recent = any(
            int(game['year']) >= 2020 if game['year'].isdigit() else False 
            for game in games
        )
        
        if has_recent:
            score += 20000
        
        return score
    
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
            has_ps4 = False
            has_steam = False
            
            for p in platforms_data:
                platform_info = p.get('platform', {})
                platform_name = platform_info.get('name', '')
                
                if 'PlayStation 5' in platform_name:
                    has_ps5 = True
                elif 'PlayStation 4' in platform_name:
                    has_ps4 = True
                elif 'PC' in platform_name:
                    has_steam = True
            
            # Construir lista de plataformas disponibles
            if has_ps5:
                platforms.append('PS5')
            if has_ps4 and not has_ps5:  # Solo mostrar PS4 si no tiene PS5
                platforms.append('PS4')
            if has_steam:
                platforms.append('Steam')
            
            # IMPORTANTE: NO filtrar por plataforma aquí
            # Dejar que todos los juegos pasen, el filtro se hará al registrar
            if not platforms:
                return None  # Solo excluir si NO tiene ninguna plataforma
            
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
                'added': added,
                'image': background_image
            }
            
        except Exception as e:
            print(f'Error formateando juego: {e}')
            return None
    ############
    def _detect_category(self, game: Dict, year: str, metacritic: int) -> str:
        try:
            # 1. RETRO: Prioridad por año
            if year.isdigit() and int(year) <= 2005:
                return 'Retro'
            
            name_lower = game.get('name', '').lower()
            genres = [g.get('name', '').lower() for g in game.get('genres', [])]
            tags = [t.get('name', '').lower() for t in game.get('tags', [])]
            publishers = [p.get('name', '').lower() for p in game.get('publishers', [])]
            developers = [d.get('name', '').lower() for d in game.get('developers', [])]

            # --- DEBUG: Esto imprimirá en tu consola qué está viendo el bot ---
            # print(f"Analizando: {name_lower} | Géneros: {genres} | Publishers: {publishers}")

            # --- PASO 1: ¿ES INDIE? (Ahora va PRIMERO) ---
            # Si RAWG dice que es Indie, le creemos a muerte (ej. Hollow Knight, V Rising)
            is_indie_by_rawg = 'indie' in genres or 'indie' in tags
            is_indie_by_list = any(any(i in p for i in self.indie_publishers) for p in publishers + developers)

            # --- PASO 2: ¿ES AAA? ---
            is_aaa_brand = any(f in name_lower for f in self.aaa_franchises)
            is_aaa_pub = any(any(aaa in p for aaa in self.aaa_publishers) for p in publishers + developers)

            # Lógica de decisión:
            # Si es de una empresa gigante (Sony, Ubisoft, etc), es AAA aunque diga indie
            if is_aaa_pub or is_aaa_brand:
                return 'Aaa'
            
            # Si no es empresa gigante y RAWG dice que es indie, es INDIE
            if is_indie_by_rawg or is_indie_by_list:
                return 'Indie'

            # --- PASO 3: ¿POR QUÉ HOLLOW KNIGHT SALE AAA? ---
            # Si aún tienes líneas que digan "if added > 100000" o "if metacritic > 80",
            # BORRALAS. Esas reglas son las que confunden a los indies buenos con AAA.

            # Si no es AAA ni Indie, es el término medio: AA
            return 'Aa'

        except Exception as e:
            print(f'Error detectando categoría: {e}')
            return 'Aa'
        ###############
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para comparación"""
        if not text:
            return ''
        
        return (
            text.lower()
            .replace('™', '')
            .replace('®', '')
            .replace(':', '')
            .replace('-', ' ')
            .replace('.', '')
            .replace('part i', 'part 1')
            .replace('part ii', 'part 2')
            .replace('part iii', 'part 3')
            .strip()
        )
    
    def _is_strong_name_match(self, query: str, game_name: str) -> bool:
        """Verifica si el nombre del juego coincide fuertemente con la búsqueda"""
        q = self._normalize_text(query)
        name = self._normalize_text(game_name)
        
        if not q or not name:
            return False
        
        # Coincidencia directa
        if q in name or name in q:
            return True
        
        # Coincidencia por palabras clave (>= 60%)
        q_words = set(q.split())
        name_words = set(name.split())
        
        if not q_words:
            return False
        
        common = q_words.intersection(name_words)
        similarity = len(common) / len(q_words)
        
        return similarity >= 0.6
    
    def has_platform(self, game_platforms: List[str], target_platform: str) -> bool:
        """Verifica si un juego está disponible en la plataforma especificada"""
        
        if target_platform == 'PS5':
            return 'PS5' in game_platforms or 'PS4' in game_platforms
        elif target_platform == 'Steam':
            return 'Steam' in game_platforms
        
        return False

# Instancia global del cliente
rawg_client = RAWGClient()