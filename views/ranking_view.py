import discord
from discord import ui
from models.game import Game
from models.user import User
import config

class RankingView(ui.View):
    """Vista principal del ranking con paginación"""
    
    def __init__(self, users: list, page: int = 0):
        super().__init__(timeout=300)  # 5 minutos
        self.users = users
        self.page = page
        self.max_pages = (len(users) - 1) // 5 + 1
        
        # Actualizar estado de botones
        self.update_buttons()
    
    def update_buttons(self):
        """Actualiza el estado de los botones según la página actual"""
        # Deshabilitar botón anterior si estamos en la primera página
        self.previous_button.disabled = (self.page == 0)
        
        # Deshabilitar botón siguiente si estamos en la última página
        self.next_button.disabled = (self.page >= self.max_pages - 1)
    
    def get_embed(self) -> discord.Embed:
        """Genera el embed del ranking para la página actual"""
        # Calcular usuarios de esta página
        start_idx = self.page * 5
        end_idx = min(start_idx + 5, len(self.users))
        page_users = self.users[start_idx:end_idx]
        
        embed = discord.Embed(
            title=f"🏆 RANKING DEL CONCURSO 2025-2027",
            description=f"Clasificación actual • Página {self.page + 1}/{self.max_pages}",
            color=config.COLORES['info']
        )
        
        # Agregar cada usuario
        medals = {0: '🥇', 1: '🥈', 2: '🥉'}
        
        for i, user in enumerate(page_users):
            actual_position = start_idx + i
            medal = medals.get(actual_position, f'**{actual_position + 1}.**')
            elkie_marker = " 👑" if user.is_elkie else ""
            
            # Barra de progreso
            if self.users[0].total_points > 0:
                percentage = int((user.total_points / self.users[0].total_points) * 100)
                filled = percentage // 10
                bar = "▰" * filled + "▱" * (10 - filled)
            else:
                bar = "▱" * 10
            
            # Información del usuario
            value = f"{bar}\n"
            value += f"💰 **{user.total_points}** pts • 🎮 **{user.total_games}** juegos{elkie_marker}\n"
            value += f"*Usa el botón debajo para ver sus juegos*"
            
            embed.add_field(
                name=f"{medal} {user.username}",
                value=value,
                inline=False
            )
        
        # Footer
        total_players = len(self.users)
        total_games = sum(u.total_games for u in self.users)
        
        embed.set_footer(text=f"👥 {total_players} participantes • 🎮 {total_games} juegos totales")
        
        return embed
    
    @ui.button(label="◀️ Anterior", style=discord.ButtonStyle.gray, custom_id="previous")
    async def previous_button(self, interaction: discord.Interaction, button: ui.Button):
        """Ir a la página anterior"""
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            
            # Limpiar botones de "Ver Detalles" anteriores
            self.clear_detail_buttons()
            self.add_detail_buttons()
            
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="▶️ Siguiente", style=discord.ButtonStyle.gray, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        """Ir a la página siguiente"""
        if self.page < self.max_pages - 1:
            self.page += 1
            self.update_buttons()
            
            # Actualizar botones de detalles
            self.clear_detail_buttons()
            self.add_detail_buttons()
            
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    def clear_detail_buttons(self):
        """Elimina los botones de ver detalles"""
        # Mantener solo los botones de navegación (primeros 2)
        while len(self.children) > 2:
            self.remove_item(self.children[-1])
    
    def add_detail_buttons(self):
        """Agrega botones de 'Ver Detalles' para cada usuario de la página"""
        start_idx = self.page * 5
        end_idx = min(start_idx + 5, len(self.users))
        page_users = self.users[start_idx:end_idx]
        
        for i, user in enumerate(page_users):
            button = ui.Button(
                label=f"📊 {user.username}",
                style=discord.ButtonStyle.primary,
                custom_id=f"details_{user.discord_id}",
                row=1 if i < 3 else 2  # Dividir en 2 filas
            )
            
            # Crear callback dinámico
            async def detail_callback(interaction: discord.Interaction, user_data=user):
                await self.show_user_details(interaction, user_data)
            
            button.callback = detail_callback
            self.add_item(button)
    
    async def show_user_details(self, interaction: discord.Interaction, user: User):
        """Muestra los detalles de un usuario específico"""
        # Obtener juegos del usuario
        games = await Game.get_by_user(user.discord_id, status='APPROVED')
        
        if not games:
            embed = discord.Embed(
                title=f"{config.EMOJIS['info']} {user.username}",
                description="Este usuario aún no tiene juegos aprobados.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Crear vista de detalles
        detail_view = UserDetailView(user, games, self)
        await interaction.response.send_message(
            embed=detail_view.get_embed(),
            view=detail_view,
            ephemeral=True
        )


class UserDetailView(ui.View):
    """Vista de detalles de un usuario con sus juegos"""
    
    def __init__(self, user: User, games: list, parent_view: RankingView):
        super().__init__(timeout=180)
        self.user = user
        self.games = games
        self.parent_view = parent_view
        self.page = 0
        self.max_pages = (len(games) - 1) // 5 + 1
        
        self.update_buttons()
    
    def update_buttons(self):
        """Actualiza estado de botones de paginación"""
        self.previous_game.disabled = (self.page == 0)
        self.next_game.disabled = (self.page >= self.max_pages - 1)
    
    def get_embed(self) -> discord.Embed:
        """Genera embed con los juegos del usuario"""
        # Calcular juegos de esta página
        start_idx = self.page * 5
        end_idx = min(start_idx + 5, len(self.games))
        page_games = self.games[start_idx:end_idx]
        
        embed = discord.Embed(
            title=f"🎮 Juegos de {self.user.username}",
            description=f"Página {self.page + 1}/{self.max_pages}",
            color=config.COLORES['aprobado']
        )
        
        # Estadísticas generales
        stats_text = (
            f"💰 **{self.user.total_points}** puntos totales\n"
            f"🎮 **{self.user.total_games}** juegos completados"
        )
        embed.add_field(name="📊 Estadísticas", value=stats_text, inline=False)
        
        # Breakdown por categoría
        categories = {}
        platinos = 0
        for game in self.games:
            categories[game.category] = categories.get(game.category, 0) + 1
            if game.has_platinum:
                platinos += 1
        
        breakdown_text = ""
        for cat, count in categories.items():
            emoji = config.EMOJIS.get(cat.lower(), '🎮')
            breakdown_text += f"{emoji} {cat}: {count} • "
        
        if platinos > 0:
            breakdown_text += f"{config.EMOJIS['platino']} Platinos: {platinos}"
        
        embed.add_field(name="🎯 Breakdown", value=breakdown_text.rstrip(' • '), inline=False)
        
        # Mostrar juegos de esta página
        for i, game in enumerate(page_games):
            categoria_emoji = config.EMOJIS.get(game.category.lower(), '🎮')
            platino_emoji = f" {config.EMOJIS['platino']}" if game.has_platinum else ""
            
            game_info = (
                f"{categoria_emoji} **{game.category}** • {game.platform}\n"
                f"💰 {game.total_points} pts{platino_emoji}"
            )
            
            embed.add_field(
                name=f"{start_idx + i + 1}. {game.game_name}",
                value=game_info,
                inline=False
            )
        
        # Usar la imagen del primer juego como thumbnail
        if page_games and hasattr(page_games[0], 'image_url') and page_games[0].image_url:
            embed.set_thumbnail(url=page_games[0].image_url)
        
        embed.set_footer(text=f"Total: {len(self.games)} juegos")
        
        return embed
    
    @ui.button(label="◀️", style=discord.ButtonStyle.gray, custom_id="prev_game")
    async def previous_game(self, interaction: discord.Interaction, button: ui.Button):
        """Página anterior de juegos"""
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="▶️", style=discord.ButtonStyle.gray, custom_id="next_game")
    async def next_game(self, interaction: discord.Interaction, button: ui.Button):
        """Página siguiente de juegos"""
        if self.page < self.max_pages - 1:
            self.page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="🔙 Volver al Ranking", style=discord.ButtonStyle.secondary, custom_id="back")
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        """Volver al ranking"""
        await interaction.response.edit_message(
            content="Volviendo al ranking...",
            embed=None,
            view=None
        )