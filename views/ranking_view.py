import discord
from discord import ui
from models.game import Game
from models.user import User
import config


class RankingTabView(ui.View):
    """Vista principal del ranking con pestañas"""
    
    def __init__(self, users: list, all_games: list):
        super().__init__(timeout=300)
        self.users = users
        self.all_games = all_games
        self.current_tab = "players"  # players, stats, category
        self.players_page = 0
        self.max_pages = (len(users) - 1) // 5 + 1
        
        self.update_all_buttons()
    
    def update_all_buttons(self):
        """Actualiza estado de todos los botones"""
        # Actualizar botones de pestañas (resaltar actual)
        self.players_tab_btn.style = discord.ButtonStyle.primary if self.current_tab == "players" else discord.ButtonStyle.secondary
        self.stats_tab_btn.style = discord.ButtonStyle.primary if self.current_tab == "stats" else discord.ButtonStyle.secondary
        self.category_tab_btn.style = discord.ButtonStyle.primary if self.current_tab == "category" else discord.ButtonStyle.secondary
        
        # Actualizar navegación
        if self.current_tab == "players":
            self.prev_btn.disabled = (self.players_page == 0)
            self.next_btn.disabled = (self.players_page >= self.max_pages - 1)
            self.prev_btn.style = discord.ButtonStyle.gray
            self.next_btn.style = discord.ButtonStyle.gray
        else:
            self.prev_btn.disabled = True
            self.next_btn.disabled = True
        
        # Limpiar y agregar botones de biblioteca si estamos en players
        self.clear_library_buttons()
        if self.current_tab == "players":
            self.add_library_buttons()
    
    def get_embed(self) -> discord.Embed:
        """Genera el embed según la pestaña actual"""
        if self.current_tab == "players":
            return self.get_players_embed()
        elif self.current_tab == "stats":
            return self.get_stats_embed()
        elif self.current_tab == "category":
            return self.get_category_embed()
    
    def get_players_embed(self) -> discord.Embed:
        """Embed de ranking de jugadores"""
        start_idx = self.players_page * 5
        end_idx = min(start_idx + 5, len(self.users))
        page_users = self.users[start_idx:end_idx]
        
        embed = discord.Embed(
            title="🏆 RANKING DEL CONCURSO 2025-2027",
            description=f"**👥 Top Players** • Página {self.players_page + 1}/{self.max_pages}",
            color=config.COLORES['info']
        )
        
        medals = {0: '🥇', 1: '🥈', 2: '🥉'}
        
        for i, user in enumerate(page_users):
            actual_position = start_idx + i
            medal = medals.get(actual_position, f'**{actual_position + 1}.**')
            elkie_marker = " 👑" if user.is_elkie else ""
            
            if self.users[0].total_points > 0:
                percentage = int((user.total_points / self.users[0].total_points) * 100)
                filled = percentage // 10
                bar = "▰" * filled + "▱" * (10 - filled)
            else:
                bar = "▱" * 10
            
            value = f"{bar}\n"
            value += f"💰 **{user.total_points}** pts • 🎮 **{user.total_games}** juegos{elkie_marker}\n"
            value += f"*Click 📚 para ver su biblioteca*"
            
            embed.add_field(
                name=f"{medal} {user.username}",
                value=value,
                inline=False
            )
        
        total_players = len(self.users)
        total_games = sum(u.total_games for u in self.users)
        
        embed.set_footer(text=f"👥 {total_players} participantes • 🎮 {total_games} juegos totales")
        
        return embed
    
    def get_stats_embed(self) -> discord.Embed:
        """Embed de estadísticas generales"""
        embed = discord.Embed(
            title="🏆 RANKING DEL CONCURSO 2025-2027",
            description="**📊 Estadísticas Generales**",
            color=config.COLORES['aprobado']
        )
        
        # Estadísticas generales
        total_games = len(self.all_games)
        total_points = sum(user.total_points for user in self.users)
        total_platinos = sum(1 for game in self.all_games if game.has_platinum)
        promedio = round(total_games / len(self.users), 1) if self.users else 0
        
        stats_text = (
            f"🎮 **{total_games}** juegos completados\n"
            f"💰 **{total_points}** puntos totales\n"
            f"🏆 **{total_platinos}** platinos obtenidos\n"
            f"📊 **{promedio}** juegos por persona"
        )
        
        embed.add_field(
            name="📈 Resumen Global",
            value=stats_text,
            inline=False
        )
        
        # Récords
        if self.users:
            most_games = max(self.users, key=lambda x: x.total_games)
            most_points = max(self.users, key=lambda x: x.total_points)
            
            records_text = (
                f"🎮 **Más juegos:** {most_games.username} ({most_games.total_games})\n"
                f"💰 **Más puntos:** {most_points.username} ({most_points.total_points})"
            )
            
            embed.add_field(
                name="🏅 Récords",
                value=records_text,
                inline=False
            )
        
        # Premios
        if self.users and self.users[0].is_elkie:
            premio_text = "🥇 1er lugar: **$30 USD**\n🥈 2do lugar: **$20 USD** (Regla Elkie activa 👑)"
        else:
            premio_text = "🥇 1er lugar: **$30 USD**"
        
        embed.add_field(
            name="🏆 Premios",
            value=premio_text,
            inline=False
        )
        
        return embed
    
    def get_category_embed(self) -> discord.Embed:
        """Embed de breakdown por categorías"""
        embed = discord.Embed(
            title="🏆 RANKING DEL CONCURSO 2025-2027",
            description="**🎮 Análisis por Categoría**",
            color=0x57F287  # Verde
        )
        
        # Contar por categorías
        categories = {}
        platforms = {}
        
        for game in self.all_games:
            categories[game.category] = categories.get(game.category, 0) + 1
            platforms[game.platform] = platforms.get(game.platform, 0) + 1
        
        # Categorías
        if categories:
            cat_text = ""
            total_games = len(self.all_games)
            sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            
            for cat, count in sorted_cats:
                emoji = config.EMOJIS.get(cat.lower(), '🎮')
                percentage = round((count / total_games) * 100)
                filled = percentage // 10
                bar = "▰" * filled + "▱" * (10 - filled)
                
                cat_text += f"{emoji} **{cat}**\n{bar} {percentage}% ({count} juegos)\n\n"
            
            embed.add_field(
                name="📊 Por Categoría",
                value=cat_text,
                inline=False
            )
        
        # Plataformas
        if platforms:
            plat_text = ""
            total_games = len(self.all_games)
            sorted_plats = sorted(platforms.items(), key=lambda x: x[1], reverse=True)
            
            for plat, count in sorted_plats:
                emoji = config.EMOJIS.get(plat.lower(), '🎮')
                percentage = round((count / total_games) * 100)
                filled = percentage // 10
                bar = "▰" * filled + "▱" * (10 - filled)
                
                plat_text += f"{emoji} **{plat}**\n{bar} {percentage}% ({count} juegos)\n\n"
            
            embed.add_field(
                name="💻 Por Plataforma",
                value=plat_text,
                inline=False
            )
        
        return embed
    
    # ==================== BOTONES DE PESTAÑAS ====================
    
    @ui.button(label="Top Players", emoji="👥", style=discord.ButtonStyle.primary, custom_id="tab_players", row=0)
    async def players_tab_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Cambiar a pestaña de jugadores"""
        self.current_tab = "players"
        self.update_all_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="Estadísticas", emoji="📊", style=discord.ButtonStyle.secondary, custom_id="tab_stats", row=0)
    async def stats_tab_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Cambiar a pestaña de estadísticas"""
        self.current_tab = "stats"
        self.update_all_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="Por Categoría", emoji="🎮", style=discord.ButtonStyle.secondary, custom_id="tab_category", row=0)
    async def category_tab_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Cambiar a pestaña de categorías"""
        self.current_tab = "category"
        self.update_all_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    # ==================== NAVEGACIÓN ====================
    
    @ui.button(label="◀️", style=discord.ButtonStyle.gray, custom_id="prev", row=1)
    async def prev_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Página anterior (solo en players)"""
        if self.current_tab == "players" and self.players_page > 0:
            self.players_page -= 1
            self.update_all_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="▶️", style=discord.ButtonStyle.gray, custom_id="next", row=1)
    async def next_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Página siguiente (solo en players)"""
        if self.current_tab == "players" and self.players_page < self.max_pages - 1:
            self.players_page += 1
            self.update_all_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    # ==================== BOTONES DE BIBLIOTECA ====================
    
    def clear_library_buttons(self):
        """Elimina botones de biblioteca"""
        while len(self.children) > 5:  # Mantener solo pestañas + navegación
            self.remove_item(self.children[-1])
    
    def add_library_buttons(self):
        """Agrega botones de biblioteca para usuarios de la página actual"""
        start_idx = self.players_page * 5
        end_idx = min(start_idx + 5, len(self.users))
        page_users = self.users[start_idx:end_idx]
        
        for i, user in enumerate(page_users):
            button = ui.Button(
                label=user.username[:20],
                emoji="📚",
                style=discord.ButtonStyle.success,
                custom_id=f"lib_{user.discord_id}",
                row=2 if i < 3 else 3
            )
            
            async def lib_callback(interaction: discord.Interaction, user_data=user):
                await self.show_library(interaction, user_data)
            
            button.callback = lib_callback
            self.add_item(button)
    
    async def show_library(self, interaction: discord.Interaction, user: User):
        """Muestra biblioteca del usuario"""
        games = await Game.get_by_user(user.discord_id, status='APPROVED')
        
        if not games:
            embed = discord.Embed(
                title=f"{config.EMOJIS['info']} {user.username}",
                description="Este usuario aún no tiene juegos aprobados.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Usar las vistas existentes de biblioteca
        library_view = GameLibraryView(user, games, self)
        await interaction.response.send_message(
            embed=library_view.get_embed(),
            view=library_view,
            ephemeral=True
        )
#######################################

class GameLibraryView(ui.View):
    """Vista de biblioteca - Lista de juegos con imágenes"""
    
    def __init__(self, user: User, games: list, parent_view: RankingTabView):
        super().__init__(timeout=180)
        self.user = user
        self.games = games
        self.parent_view = parent_view
        self.page = 0
        self.games_per_page = 3  # 3 juegos por página para que se vean las imágenes
        self.max_pages = (len(games) - 1) // self.games_per_page + 1
        
        self.update_buttons()
    
    def update_buttons(self):
        """Actualiza estado de botones de paginación"""
        self.previous_game.disabled = (self.page == 0)
        self.next_game.disabled = (self.page >= self.max_pages - 1)
        
        # Limpiar botones de detalles viejos
        self.clear_detail_buttons()
        self.add_game_detail_buttons()
    
    def get_embed(self) -> discord.Embed:
        """Genera embed de biblioteca con lista visual de juegos"""
        start_idx = self.page * self.games_per_page
        end_idx = min(start_idx + self.games_per_page, len(self.games))
        page_games = self.games[start_idx:end_idx]
        
        embed = discord.Embed(
            title=f"📚 Biblioteca de {self.user.username}",
            description=f"Página {self.page + 1}/{self.max_pages}",
            color=config.COLORES['aprobado']
        )
        
        # Estadísticas en el header
        categories = {}
        platinos = 0
        for game in self.games:
            categories[game.category] = categories.get(game.category, 0) + 1
            if game.has_platinum:
                platinos += 1
        
        stats_text = f"💰 **{self.user.total_points}** pts • 🎮 **{self.user.total_games}** juegos"
        if platinos > 0:
            stats_text += f" • 🏆 **{platinos}** platinos"
        
        embed.add_field(name="📊 Estadísticas", value=stats_text, inline=False)
        
        # Mostrar cada juego con su imagen
        for i, game in enumerate(page_games):
            categoria_emoji = config.EMOJIS.get(game.category.lower(), '🎮')
            platino_emoji = "🏆" if game.has_platinum else ""
            
            # Información del juego
            game_info = f"{categoria_emoji} **{game.category}** • {game.platform}\n"
            game_info += f"💰 **{game.total_points}** pts {platino_emoji}\n"
            game_info += f"👁️ *Click en 'Ver Detalles' para pantalla completa*"
            
            embed.add_field(
                name=f"{start_idx + i + 1}. {game.game_name}",
                value=game_info,
                inline=False
            )
            
            # Si el juego tiene imagen, mostrarla como thumbnail (solo el primero)
            if i == 0 and game.image_url:
                embed.set_thumbnail(url=game.image_url)
        
        embed.set_footer(text=f"Total: {len(self.games)} juegos • Usa los botones para navegar")
        
        return embed
    
    def clear_detail_buttons(self):
        """Elimina botones de detalles de juegos"""
        # Mantener solo los 3 primeros botones (navegación + volver)
        while len(self.children) > 3:
            self.remove_item(self.children[-1])
    
    def add_game_detail_buttons(self):
        """Agrega botones para ver detalles de cada juego en la página"""
        start_idx = self.page * self.games_per_page
        end_idx = min(start_idx + self.games_per_page, len(self.games))
        page_games = self.games[start_idx:end_idx]
        
        for i, game in enumerate(page_games):
            # Truncar nombre del juego para el botón
            game_name_short = game.game_name[:15] + "..." if len(game.game_name) > 15 else game.game_name
            
            button = ui.Button(
                label=f"👁️ {game_name_short}",
                style=discord.ButtonStyle.success,
                custom_id=f"detail_{game.id}",
                row=3 if i < 2 else 4
            )
            
            async def detail_callback(interaction: discord.Interaction, game_data=game, game_idx=start_idx + i):
                await self.show_game_detail(interaction, game_data, game_idx)
            
            button.callback = detail_callback
            self.add_item(button)
    
    async def show_game_detail(self, interaction: discord.Interaction, game: Game, game_index: int):
        """Muestra vista detallada de un juego específico (full screen)"""
        detail_view = GameDetailView(self.user, self.games, game_index, self)
        await interaction.response.edit_message(
            embed=detail_view.get_embed(),
            view=detail_view
        )
    
    @ui.button(label="◀️", style=discord.ButtonStyle.gray, custom_id="prev_game", row=0)
    async def previous_game(self, interaction: discord.Interaction, button: ui.Button):
        """Página anterior de juegos"""
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="▶️", style=discord.ButtonStyle.gray, custom_id="next_game", row=0)
    async def next_game(self, interaction: discord.Interaction, button: ui.Button):
        """Página siguiente de juegos"""
        if self.page < self.max_pages - 1:
            self.page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="🔙 Volver al Ranking", style=discord.ButtonStyle.secondary, custom_id="back", row=0)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        """Volver al ranking"""
        await interaction.response.edit_message(
            content="✅ Volviendo al ranking...",
            embed=None,
            view=None,
            delete_after=2
        )


class GameDetailView(ui.View):
    """Vista detallada de un juego - Pantalla completa estilo carrusel"""
    
    def __init__(self, user: User, games: list, current_index: int, library_view: GameLibraryView):
        super().__init__(timeout=180)
        self.user = user
        self.games = games
        self.current_index = current_index
        self.library_view = library_view
        
        self.update_buttons()
    
    def update_buttons(self):
        """Actualiza botones de navegación"""
        self.previous_game_btn.disabled = (self.current_index == 0)
        self.next_game_btn.disabled = (self.current_index >= len(self.games) - 1)
    
    def get_embed(self) -> discord.Embed:
        """Genera embed de detalle full screen del juego"""
        game = self.games[self.current_index]
        
        # Color según categoría
        color_map = {
            'AAA': config.COLORES['aprobado'],
            'AA': config.COLORES['info'],
            'Indie': 0xFF6B9D,  # Rosa
            'Retro': 0xFFD700   # Dorado
        }
        color = color_map.get(game.category, config.COLORES['info'])
        
        embed = discord.Embed(
            title=f"🎮 {game.game_name}",
            color=color
        )
        
        # IMAGEN GRANDE (la parte más importante)
        if game.image_url:
            embed.set_image(url=game.image_url)
        
        # Información del juego
        categoria_emoji = config.EMOJIS.get(game.category.lower(), '🎮')
        
        info_principal = f"{categoria_emoji} **{game.category}**"
        info_principal += f" • 💻 **{game.platform}**"
        if game.has_platinum:
            info_principal += f" • 🏆 **Platino**"
        
        embed.add_field(
            name="📋 Información",
            value=info_principal,
            inline=False
        )
        
        # Puntos
        embed.add_field(
            name="💰 Puntos",
            value=f"**{game.total_points}** pts",
            inline=True
        )
        
        # Fecha de registro
        if game.submission_date:
            fecha = game.submission_date.split(' ')[0] if ' ' in str(game.submission_date) else str(game.submission_date)
            embed.add_field(
                name="📅 Registrado",
                value=fecha,
                inline=True
            )
        
        # Footer con posición
        embed.set_footer(
            text=f"Juego {self.current_index + 1} de {len(self.games)} • Biblioteca de {self.user.username}"
        )
        
        return embed
    
    @ui.button(label="◀️ Anterior", style=discord.ButtonStyle.primary, custom_id="prev_detail")
    async def previous_game_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Ir al juego anterior"""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="▶️ Siguiente", style=discord.ButtonStyle.primary, custom_id="next_detail")
    async def next_game_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Ir al juego siguiente"""
        if self.current_index < len(self.games) - 1:
            self.current_index += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="📚 Volver a Biblioteca", style=discord.ButtonStyle.secondary, custom_id="back_lib")
    async def back_to_library(self, interaction: discord.Interaction, button: ui.Button):
        """Volver a la vista de biblioteca"""
        await interaction.response.edit_message(
            embed=self.library_view.get_embed(),
            view=self.library_view
        )