import discord
from discord import ui
from models.game import Game
from models.user import User
import config
from datetime import datetime


class DashboardView(ui.View):
    """Vista del dashboard con select menu"""
    
    def __init__(self, users: list, all_games: list):
        super().__init__(timeout=300)
        self.users = users
        self.all_games = all_games
        
        # Agregar select menu
        self.add_item(DashboardSelectMenu())
    
    def get_main_embed(self) -> discord.Embed:
        """Embed principal del dashboard"""
        embed = discord.Embed(
            title="📊 DASHBOARD DEL CONCURSO 2025-2027",
            description="Selecciona una sección del menú para ver información detallada.",
            color=config.COLORES['info']
        )
        
        # Secciones disponibles
        sections = [
            "📊 **Resumen General** - Estadísticas principales y top 3",
            "🏆 **Top 5 Ranking** - Clasificación completa con barras de progreso",
            "📈 **Análisis Detallado** - Breakdown por categorías y plataformas",
            "⏰ **Progreso Temporal** - Tiempo transcurrido y proyecciones",
            "🏅 **Récords** - Logros y estadísticas especiales",
        ]
        
        embed.add_field(
            name="📂 Secciones Disponibles",
            value="\n".join(sections),
            inline=False
        )
        
        # Stats rápidas en el inicio
        total_games = len(self.all_games)
        total_points = sum(u.total_points for u in self.users)
        total_platinos = sum(1 for g in self.all_games if g.has_platinum)
        
        quick_stats = (
            f"🎮 **{total_games}** juegos  •  "
            f"💰 **{total_points}** pts  •  "
            f"🏆 **{total_platinos}** platinos"
        )
        
        embed.add_field(
            name="⚡ Vista Rápida",
            value=quick_stats,
            inline=False
        )
        
        embed.set_footer(text="💡 Usa el menú desplegable para navegar entre secciones")
        
        return embed


class DashboardSelectMenu(ui.Select):
    """Menú desplegable para el dashboard"""
    
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Inicio",
                description="Volver al menú principal",
                emoji="🏠",
                value="main"
            ),
            discord.SelectOption(
                label="Resumen General",
                description="Estadísticas principales y top 3",
                emoji="📊",
                value="summary"
            ),
            discord.SelectOption(
                label="Top 5 Ranking",
                description="Clasificación completa",
                emoji="🏆",
                value="ranking"
            ),
            discord.SelectOption(
                label="Análisis Detallado",
                description="Breakdown por categorías y plataformas",
                emoji="📈",
                value="analysis"
            ),
            discord.SelectOption(
                label="Progreso Temporal",
                description="Tiempo transcurrido y proyecciones",
                emoji="⏰",
                value="progress"
            ),
            discord.SelectOption(
                label="Récords",
                description="Logros y estadísticas especiales",
                emoji="🏅",
                value="records"
            ),
        ]
        
        super().__init__(
            placeholder="📂 Selecciona una sección...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="dashboard_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Maneja la selección del menú"""
        selected = self.values[0]
        
        if selected == "main":
            embed = self.view.get_main_embed()
        elif selected == "summary":
            embed = self.get_summary_embed()
        elif selected == "ranking":
            embed = self.get_ranking_embed()
        elif selected == "analysis":
            embed = self.get_analysis_embed()
        elif selected == "progress":
            embed = self.get_progress_embed()
        elif selected == "records":
            embed = self.get_records_embed()
        
        await interaction.response.edit_message(embed=embed, view=self.view)
    
    def get_summary_embed(self) -> discord.Embed:
        """Resumen general"""
        embed = discord.Embed(
            title="📊 RESUMEN GENERAL",
            color=config.COLORES['info']
        )
        
        users = self.view.users
        games = self.view.all_games
        
        # Estadísticas principales
        total_games = len(games)
        total_points = sum(u.total_points for u in users)
        total_platinos = sum(1 for g in games if g.has_platinum)
        promedio = round(total_games / len(users), 1) if users else 0
        
        stats_text = (
            f"🎮 **{total_games}** juegos completados\n"
            f"💰 **{total_points}** puntos totales\n"
            f"🏆 **{total_platinos}** platinos obtenidos\n"
            f"📊 **{promedio}** juegos por persona"
        )
        
        embed.add_field(
            name="📈 Estadísticas Globales",
            value=stats_text,
            inline=False
        )
        
        # Top 3
        top3_text = ""
        medals = {0: '🥇', 1: '🥈', 2: '🥉'}
        
        for i, user in enumerate(users[:3]):
            medal = medals.get(i, '')
            elkie = " 👑" if user.is_elkie else ""
            top3_text += f"{medal} **{user.username}**{elkie}\n"
            top3_text += f"💰 {user.total_points} pts • 🎮 {user.total_games} juegos\n\n"
        
        if top3_text:
            embed.add_field(
                name="🏆 Top 3 Participantes",
                value=top3_text,
                inline=False
            )
        
        # Premios
        if users and users[0].is_elkie:
            premio_text = "🥇 1er lugar: **$30 USD**\n🥈 2do lugar: **$20 USD** (Regla Elkie 👑)"
        else:
            premio_text = "🥇 1er lugar: **$30 USD**"
        
        embed.add_field(
            name="🏆 Premios",
            value=premio_text,
            inline=False
        )
        
        embed.set_footer(text="💡 Usa el menú para ver más detalles")
        
        return embed
    
    def get_ranking_embed(self) -> discord.Embed:
        """Top 5 ranking"""
        embed = discord.Embed(
            title="🏆 TOP 5 RANKING",
            color=config.COLORES['aprobado']
        )
        
        users = self.view.users[:5]
        medals = {0: '🥇', 1: '🥈', 2: '🥉'}
        
        ranking_text = ""
        
        for i, user in enumerate(users):
            medal = medals.get(i, f'**{i+1}.**')
            elkie = " 👑" if user.is_elkie else ""
            
            # Barra de progreso
            if self.view.users[0].total_points > 0:
                percentage = int((user.total_points / self.view.users[0].total_points) * 100)
                filled = percentage // 10
                bar = "▰" * filled + "▱" * (10 - filled)
            else:
                bar = "▱" * 10
                percentage = 0
            
            ranking_text += f"\n{medal} **{user.username}**{elkie}\n"
            ranking_text += f"{bar} {percentage}%\n"
            ranking_text += f"💰 {user.total_points} pts • 🎮 {user.total_games} juegos\n"
        
        embed.add_field(
            name="",
            value=ranking_text,
            inline=False
        )
        
        embed.set_footer(text=f"Total: {len(self.view.users)} participantes")
        
        return embed
    
    def get_analysis_embed(self) -> discord.Embed:
        """Análisis detallado"""
        embed = discord.Embed(
            title="📈 ANÁLISIS DETALLADO",
            color=0x57F287  # Verde
        )
        
        games = self.view.all_games
        
        # Por categorías
        categories = {}
        for game in games:
            categories[game.category] = categories.get(game.category, 0) + 1
        
        if categories:
            cat_text = ""
            total = len(games)
            sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            
            for cat, count in sorted_cats:
                emoji = config.EMOJIS.get(cat.lower(), '🎮')
                percentage = round((count / total) * 100)
                filled = percentage // 10
                bar = "▰" * filled + "▱" * (10 - filled)
                
                cat_text += f"{emoji} **{cat}**\n"
                cat_text += f"{bar} {percentage}% ({count})\n\n"
            
            embed.add_field(
                name="🎯 Por Categoría",
                value=cat_text,
                inline=False
            )
        
        # Por plataforma
        platforms = {}
        for game in games:
            platforms[game.platform] = platforms.get(game.platform, 0) + 1
        
        if platforms:
            plat_text = ""
            sorted_plats = sorted(platforms.items(), key=lambda x: x[1], reverse=True)
            
            for plat, count in sorted_plats:
                emoji = config.EMOJIS.get(plat.lower(), '🎮')
                percentage = round((count / total) * 100)
                filled = percentage // 10
                bar = "▰" * filled + "▱" * (10 - filled)
                
                plat_text += f"{emoji} **{plat}**\n"
                plat_text += f"{bar} {percentage}% ({count})\n\n"
            
            embed.add_field(
                name="💻 Por Plataforma",
                value=plat_text,
                inline=False
            )
        
        return embed
    
    def get_progress_embed(self) -> discord.Embed:
        """Progreso temporal"""
        embed = discord.Embed(
            title="⏰ PROGRESO DEL CONCURSO",
            color=0xFEE75C  # Amarillo
        )
        
        now = datetime.now()
        days_passed = max(1, (now - config.CONTEST_START_DATE).days)
        days_total = (config.CONTEST_END_DATE - config.CONTEST_START_DATE).days
        days_remaining = (config.CONTEST_END_DATE - now).days
        
        progress_pct = round((days_passed / days_total) * 100) if days_total > 0 else 0
        filled = progress_pct // 10
        progress_bar = "▰" * filled + "▱" * (10 - filled)
        
        tiempo_text = (
            f"**{progress_bar} {progress_pct}%**\n\n"
            f"📅 Días transcurridos: **{days_passed}**\n"
            f"⏳ Días restantes: **{days_remaining}**\n"
            f"📆 Total: **{days_total}** días"
        )
        
        embed.add_field(
            name="🕐 Progreso Temporal",
            value=tiempo_text,
            inline=False
        )
        
        # Proyección
        total_games = len(self.view.all_games)
        rate_per_day = round(total_games / days_passed, 2)
        projected_total = round(rate_per_day * days_total)
        
        proyeccion_text = (
            f"📈 Ritmo actual: **{rate_per_day}** juegos/día\n"
            f"🎯 Proyección final: **~{projected_total}** juegos\n"
            f"📊 Juegos actuales: **{total_games}**"
        )
        
        embed.add_field(
            name="📊 Proyección",
            value=proyeccion_text,
            inline=False
        )
        
        return embed
    
    def get_records_embed(self) -> discord.Embed:
        """Récords y logros"""
        embed = discord.Embed(
            title="🏅 RÉCORDS Y LOGROS",
            color=0xED4245  # Rojo
        )
        
        users = self.view.users
        games = self.view.all_games
        
        if not users:
            embed.description = "No hay récords disponibles aún."
            return embed
        
        # Récords individuales
        most_games = max(users, key=lambda x: x.total_games)
        most_points = max(users, key=lambda x: x.total_points)
        
        records_text = (
            f"🎮 **Más juegos completados:**\n"
            f"{most_games.username} - **{most_games.total_games}** juegos\n\n"
            f"💰 **Más puntos acumulados:**\n"
            f"{most_points.username} - **{most_points.total_points}** pts"
        )
        
        embed.add_field(
            name="🏆 Récords Individuales",
            value=records_text,
            inline=False
        )
        
        # Estadísticas especiales
        total_platinos = sum(1 for g in games if g.has_platinum)
        platino_users = {}
        for game in games:
            if game.has_platinum:
                platino_users[game.username] = platino_users.get(game.username, 0) + 1
        
        if platino_users:
            cazador = max(platino_users.items(), key=lambda x: x[1])
            special_text = (
                f"🏆 **Cazador de Platinos:**\n"
                f"{cazador[0]} - **{cazador[1]}** platinos\n\n"
                f"💎 **Total de platinos:** {total_platinos}"
            )
            
            embed.add_field(
                name="✨ Logros Especiales",
                value=special_text,
                inline=False
            )
        
        return embed


class RefreshButton(ui.Button):
    """Botón para actualizar el dashboard"""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Actualizar Dashboard",
            emoji="🔄",
            custom_id="refresh_dashboard"
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Recargar datos
        from models.user import User
        from models.game import Game
        
        users = await User.get_all_ranked()
        ranked_users = [u for u in users if u.total_games > 0]
        
        all_games = []
        for user in ranked_users:
            games = await Game.get_by_user(user.discord_id, status='APPROVED')
            all_games.extend(games)
        
        # Actualizar vista
        self.view.users = ranked_users
        self.view.all_games = all_games
        
        await interaction.response.edit_message(
            embed=self.view.get_main_embed(),
            view=self.view
        )