from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
import config
from models.user import User
from models.game import Game

class Ranking(commands.Cog):
    """Comandos relacionados con el ranking y estadísticas"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ranking", description="Ver el ranking general del concurso")
    async def ranking(self, interaction: discord.Interaction):
        """Muestra el ranking de todos los participantes"""
        
        users = await User.get_all_ranked()
        
        if not users or all(user.total_games == 0 for user in users):
            embed = discord.Embed(
                title=f"{config.EMOJIS['ranking']} Ranking del Concurso",
                description="Aún no hay juegos aprobados. ¡Sé el primero en registrar!",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Filtrar usuarios con al menos un juego
        ranked_users = [user for user in users if user.total_games > 0]
        
        embed = discord.Embed(
            title=f"{config.EMOJIS['ranking']} Ranking Anual 2025-2027",
            description="Clasificación actual del concurso",
            color=config.COLORES['info']
        )
        
        # Emojis de medallas
        medals = ['🥇', '🥈', '🥉']
        
        # Mostrar top participantes
        for i, user in enumerate(ranked_users[:10], 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            
            # Calcular barra de progreso visual
            MAX_BARS = 20
            FULL = "▰"
            EMPTY = "▱"
            
            if ranked_users[0].total_points > 0:
                RATIO = user.total_points / ranked_users[0].total_points
                filled = int(RATIO * MAX_BARS)
                bar = FULL * filled + EMPTY * (MAX_BARS - filled)
                percentage = int(RATIO * 100)
                bar_text = f"{bar} {percentage}%"
            else:
                bar_text = f"{EMPTY * MAX_BARS} 0%"
            
            # Marcar si es Elkie
            elkie_marker = " 👑" if user.is_elkie else ""
            
            embed.add_field(
                name=f"{medal} {user.username}{elkie_marker}",
                value=f"{bar_text} **{user.total_points}** pts ({user.total_games} juegos)",
                inline=False
            )
        
        # Información de premios
        premio_text = "\n\n🏆 **PREMIOS:**\n"
        
        if ranked_users and ranked_users[0].is_elkie:
            premio_text += (
                f"⚠️ **REGLA ESPECIAL ACTIVA:**\n"
                f"Como Elkie está en primer lugar:\n"
                f"🥇 1er puesto: Juego de $30 USD\n"
                f"🥈 2do puesto: Juego de $20 USD"
            )
        else:
            premio_text += "🥇 1er puesto: Juego de $30 USD"
        
        embed.description += premio_text
        
        # Estadísticas generales
        total_games = sum(user.total_games for user in ranked_users)
        total_points = sum(user.total_points for user in ranked_users)
        
        embed.set_footer(
            text=f"Total: {total_games} juegos • {total_points} puntos • {len(ranked_users)} participantes"
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="mi-posicion", description="Ver tu posición actual en el ranking")
    async def mi_posicion(self, interaction: discord.Interaction):
        """Muestra la posición del usuario en el ranking"""
        
        user = await User.get(interaction.user.id)
        
        if not user or user.total_games == 0:
            embed = discord.Embed(
                title=f"{config.EMOJIS['info']} Tu Posición",
                description="Aún no tienes juegos aprobados.\nUsa `/registrar` para comenzar!",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Obtener todos los usuarios rankeados
        all_users = await User.get_all_ranked()
        ranked_users = [u for u in all_users if u.total_games > 0]
        
        # Encontrar posición
        position = next((i for i, u in enumerate(ranked_users, 1) if u.discord_id == user.discord_id), None)
        
        if not position:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description="No se pudo determinar tu posición.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Emoji de posición
        position_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}.get(position, f'{position}°')
        
        embed = discord.Embed(
            title=f"{config.EMOJIS['usuario']} Tu Posición Actual",
            description=f"Estás en el puesto **{position_emoji}** de {len(ranked_users)}",
            color=config.COLORES['info']
        )
        
        # Estadísticas personales
        embed.add_field(
            name=f"{config.EMOJIS['puntos']} Puntos Totales",
            value=f"**{user.total_points}** puntos",
            inline=True
        )
        
        embed.add_field(
            name=f"{config.EMOJIS['registrar']} Juegos Completados",
            value=f"**{user.total_games}** juegos",
            inline=True
        )
        
        # Promedio de puntos por juego
        avg_points = round(user.total_points / user.total_games, 1) if user.total_games > 0 else 0
        embed.add_field(
            name="📊 Promedio",
            value=f"{avg_points} pts/juego",
            inline=True
        )
        
        # Diferencia con el primero (si no es el primero)
        if position > 1:
            first_user = ranked_users[0]
            diff_points = first_user.total_points - user.total_points
            diff_games = first_user.total_games - user.total_games
            
            embed.add_field(
                name=f"📈 Diferencia con 1° lugar",
                value=f"-{diff_points} pts ({diff_games} juegos menos)",
                inline=False
            )
        
        # Diferencia con el siguiente (si no es el último)
        if position < len(ranked_users):
            next_user = ranked_users[position]  # siguiente posición
            diff_points = user.total_points - next_user.total_points
            
            embed.add_field(
                name=f"📉 Ventaja sobre {position + 1}° lugar",
                value=f"+{diff_points} pts",
                inline=False
            )
        
        # Obtener juegos aprobados para más detalles
        games = await Game.get_by_user(user.discord_id, status='APPROVED')
        
        # Contar platinos
        platinos = sum(1 for game in games if game.has_platinum)
        recompletados = sum(1 for game in games if game.is_recompleted)
        
        stats_text = ""
        if platinos > 0:
            stats_text += f"{config.EMOJIS['platino']} {platinos} platinos\n"
        if recompletados > 0:
            stats_text += f"🔄 {recompletados} re-completados\n"
        
        if stats_text:
            embed.add_field(
                name="🎯 Logros",
                value=stats_text,
                inline=False
            )
        
        embed.set_footer(text="Usa /ranking para ver el ranking completo")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="estadisticas", description="Ver estadísticas detalladas de un usuario")
    @app_commands.describe(usuario="Usuario del que quieres ver las estadísticas (opcional)")
    async def estadisticas(self, interaction: discord.Interaction, usuario: discord.User = None):
        """Muestra estadísticas detalladas de un usuario"""
        
        target_user = usuario or interaction.user
        
        user = await User.get(target_user.id)
        
        if not user or user.total_games == 0:
            embed = discord.Embed(
                title=f"{config.EMOJIS['info']} Estadísticas",
                description=f"**{target_user.name}** aún no tiene juegos aprobados.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Obtener juegos
        games = await Game.get_by_user(user.discord_id, status='APPROVED')
        
        embed = discord.Embed(
            title=f"{config.EMOJIS['ranking']} Estadísticas de {user.username}",
            color=config.COLORES['info']
        )
        
        # Estadísticas generales
        embed.add_field(
            name=f"{config.EMOJIS['puntos']} Puntos Totales",
            value=f"**{user.total_points}** puntos",
            inline=True
        )
        
        embed.add_field(
            name=f"{config.EMOJIS['registrar']} Juegos Completados",
            value=f"**{user.total_games}** juegos",
            inline=True
        )
        
        # Calcular posición
        all_users = await User.get_all_ranked()
        ranked_users = [u for u in all_users if u.total_games > 0]
        position = next((i for i, u in enumerate(ranked_users, 1) if u.discord_id == user.discord_id), 0)
        position_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}.get(position, f'{position}°')
        
        embed.add_field(
            name="🏆 Posición",
            value=f"**{position_emoji}** lugar",
            inline=True
        )
        
        # Estadísticas por categoría
        categories = {}
        platforms = {}
        platinos = 0
        recompletados = 0
        
        for game in games:
            # Contar por categoría
            categories[game.category] = categories.get(game.category, 0) + 1
            # Contar por plataforma
            platforms[game.platform] = platforms.get(game.platform, 0) + 1
            # Contar platinos
            if game.has_platinum:
                platinos += 1
            # Contar re-completados
            if game.is_recompleted:
                recompletados += 1
        
        # Distribución por categoría
        cat_text = ""
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            emoji = config.EMOJIS.get(cat.lower(), '🎮')
            cat_text += f"{emoji} {cat}: {count}\n"
        
        embed.add_field(
            name="📊 Por Categoría",
            value=cat_text if cat_text else "N/A",
            inline=True
        )
        
        # Distribución por plataforma
        plat_text = ""
        for plat, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
            emoji = config.EMOJIS.get(plat.lower(), '🎮')
            plat_text += f"{emoji} {plat}: {count}\n"
        
        embed.add_field(
            name="🎮 Por Plataforma",
            value=plat_text if plat_text else "N/A",
            inline=True
        )
        
        # Logros especiales
        special_text = f"{config.EMOJIS['platino']} Platinos: {platinos}\n"
        if recompletados > 0:
            special_text += f"🔄 Re-completados: {recompletados}\n"
        
        avg_points = round(user.total_points / user.total_games, 1)
        special_text += f"📈 Promedio: {avg_points} pts/juego"
        
        embed.add_field(
            name="🎯 Extras",
            value=special_text,
            inline=False
        )
        
        # Top 3 juegos con más puntos
        top_games = sorted(games, key=lambda x: x.total_points, reverse=True)[:3]
        if top_games:
            top_text = ""
            for i, game in enumerate(top_games, 1):
                platino_icon = f" {config.EMOJIS['platino']}" if game.has_platinum else ""
                top_text += f"{i}. {game.game_name}{platino_icon} - {game.total_points} pts\n"
            
            embed.add_field(
                name="⭐ Top Juegos",
                value=top_text,
                inline=False
            )
        
        embed.set_footer(text=f"Miembro desde {user.join_date[:10]}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="tablero", description="Ver el dashboard completo del concurso")
    async def tablero(self, interaction: discord.Interaction):
        """Muestra un dashboard visual con todas las estadísticas del grupo"""
        
        await interaction.response.defer()
        
        # Obtener todos los usuarios
        users = await User.get_all_ranked()
        ranked_users = [user for user in users if user.total_games > 0]
        
        if not ranked_users:
            embed = discord.Embed(
                title=f"{config.EMOJIS['ranking']} Dashboard del Concurso",
                description="Aún no hay actividad. ¡Sé el primero en registrar un juego!",
                color=config.COLORES['info']
            )
            await interaction.followup.send(embed=embed)
            return
        
        # ==================== EMBED 1: RANKING ====================
        embed1 = discord.Embed(
            title=f"{config.EMOJIS['ranking']} DASHBOARD DEL CONCURSO",
            description="═══════════════════════════",
            color=config.COLORES['info']
        )
        
        # Top 5 ranking
        medals = ['🥇', '🥈', '🥉', '4.', '5.']
        ranking_text = ""
        
        for i, user in enumerate(ranked_users[:5], 1):
            medal = medals[i-1] if i <= 5 else f"{i}."
            
            # Barra de progreso
            if ranked_users[0].total_points > 0:
                progress = int((user.total_points / ranked_users[0].total_points) * 12)
                bar = "█" * progress + "░" * (12 - progress)
            else:
                bar = "░" * 12
            
            elkie_marker = " 👑" if user.is_elkie else ""
            ranking_text += f"{medal} **{user.username}**{elkie_marker}\n{bar} `{user.total_points} pts` ({user.total_games} juegos)\n\n"
        
        embed1.add_field(
            name="🏆 TOP 5 RANKING",
            value=ranking_text if ranking_text else "Sin datos",
            inline=False
        )
        
        # Información de premios
        premio_text = "💰 **PREMIOS:**\n"
        if ranked_users and ranked_users[0].is_elkie:
            premio_text += (
                "⚠️ **REGLA ESPECIAL ACTIVA**\n"
                "🥇 1er lugar: Juego de $30 USD\n"
                "🥈 2do lugar: Juego de $20 USD"
            )
        else:
            premio_text += "🥇 1er lugar: Juego de $30 USD"
        
        embed1.add_field(
            name="═══════════════════════════",
            value=premio_text,
            inline=False
        )
        
        # ==================== EMBED 2: ESTADÍSTICAS GRUPALES ====================
        embed2 = discord.Embed(
            title="📊 ESTADÍSTICAS GRUPALES",
            color=config.COLORES['info']
        )
        
        # Obtener todos los juegos aprobados
        all_games = []
        for user in ranked_users:
            games = await Game.get_by_user(user.discord_id, status='APPROVED')
            all_games.extend(games)
        
        total_games = len(all_games)
        total_points = sum(user.total_points for user in ranked_users)
        total_platinos = sum(1 for game in all_games if game.has_platinum)
        total_recompletados = sum(1 for game in all_games if game.is_recompleted)
        
        # Stats generales
        stats_text = (
            f"🎮 **Total de juegos:** {total_games}\n"
            f"💰 **Puntos totales:** {total_points}\n"
            f"🏆 **Platinos:** {total_platinos}\n"
            f"🔄 **Re-completados:** {total_recompletados}\n"
            f"👥 **Participantes:** {len(ranked_users)}\n"
            f"📈 **Promedio:** {round(total_games / len(ranked_users), 1)} juegos/persona"
        )
        
        embed2.add_field(
            name="📋 Resumen General",
            value=stats_text,
            inline=False
        )
        
        # Distribución por categoría
        categories = {}
        platforms = {}
        
        for game in all_games:
            categories[game.category] = categories.get(game.category, 0) + 1
            platforms[game.platform] = platforms.get(game.platform, 0) + 1
        
        # Por categoría
        if categories:
            cat_text = ""
            sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            for cat, count in sorted_cats:
                emoji = config.EMOJIS.get(cat.lower(), '🎮')
                percentage = round((count / total_games) * 100)
                bar = "█" * (percentage // 10) + "░" * (10 - percentage // 10)
                cat_text += f"{emoji} {cat}: {bar} {percentage}% ({count})\n"
            
            embed2.add_field(
                name="🎯 Distribución por Categoría",
                value=cat_text,
                inline=False
            )
        
        # Por plataforma
        if platforms:
            plat_text = ""
            sorted_plats = sorted(platforms.items(), key=lambda x: x[1], reverse=True)
            for plat, count in sorted_plats:
                emoji = config.EMOJIS.get(plat.lower(), '🎮')
                percentage = round((count / total_games) * 100)
                bar = "█" * (percentage // 10) + "░" * (10 - percentage // 10)
                plat_text += f"{emoji} {plat}: {bar} {percentage}% ({count})\n"
            
            embed2.add_field(
                name="💻 Distribución por Plataforma",
                value=plat_text,
                inline=False
            )
        
        # ==================== EMBED 3: RÉCORDS Y CURIOSIDADES ====================
        embed3 = discord.Embed(
            title="🏅 RÉCORDS Y DESTACADOS",
            color=config.COLORES['info']
        )
        
        # Usuario con más juegos
        most_games_user = max(ranked_users, key=lambda x: x.total_games)
        embed3.add_field(
            name="🎮 Más Juegos Completados",
            value=f"**{most_games_user.username}** - {most_games_user.total_games} juegos",
            inline=True
        )
        
        # Usuario con más puntos
        most_points_user = max(ranked_users, key=lambda x: x.total_points)
        embed3.add_field(
            name="💰 Más Puntos",
            value=f"**{most_points_user.username}** - {most_points_user.total_points} pts",
            inline=True
        )
        
        # Usuario con más platinos
        platinos_por_usuario = {}
        for user in ranked_users:
            user_games = await Game.get_by_user(user.discord_id, status='APPROVED')
            platinos_por_usuario[user.username] = sum(1 for g in user_games if g.has_platinum)
        
        if platinos_por_usuario:
            most_platinos_user = max(platinos_por_usuario.items(), key=lambda x: x[1])
            if most_platinos_user[1] > 0:
                embed3.add_field(
                    name="🏆 Cazador de Platinos",
                    value=f"**{most_platinos_user[0]}** - {most_platinos_user[1]} platinos",
                    inline=True
                )
        
        # Mejor promedio puntos/juego
        best_avg_user = max(ranked_users, key=lambda x: x.total_points / x.total_games if x.total_games > 0 else 0)
        avg = round(best_avg_user.total_points / best_avg_user.total_games, 1) if best_avg_user.total_games > 0 else 0
        embed3.add_field(
            name="📈 Mejor Promedio",
            value=f"**{best_avg_user.username}** - {avg} pts/juego",
            inline=True
        )
        
        # Juego más jugado
        game_counts = {}
        for game in all_games:
            game_counts[game.game_name] = game_counts.get(game.game_name, 0) + 1
        
        if game_counts:
            most_played = max(game_counts.items(), key=lambda x: x[1])
            if most_played[1] > 1:
                embed3.add_field(
                    name="🔥 Juego Más Popular",
                    value=f"**{most_played[0]}** ({most_played[1]} personas lo completaron)",
                    inline=False
                )
        
        # ==================== EMBED 4: PROGRESO TEMPORAL ====================
        embed4 = discord.Embed(
            title=f"{config.EMOJIS['fecha']} PROGRESO DEL CONCURSO",
            color=config.COLORES['info']
        )
        
        # Calcular días transcurridos y restantes
        from datetime import datetime
        now = datetime.now()
        days_passed = (now - config.CONTEST_START_DATE).days
        days_total = (config.CONTEST_END_DATE - config.CONTEST_START_DATE).days
        days_remaining = (config.CONTEST_END_DATE - now).days
        
        progress_pct = round((days_passed / days_total) * 100) if days_total > 0 else 0
        progress_bar = "█" * (progress_pct // 5) + "░" * (20 - progress_pct // 5)
        
        tiempo_text = (
            f"📅 **Inicio:** {config.CONTEST_START_DATE.strftime('%d/%m/%Y')}\n"
            f"📅 **Fin:** {config.CONTEST_END_DATE.strftime('%d/%m/%Y')}\n\n"
            f"⏰ **Progreso:** {progress_bar} {progress_pct}%\n"
            f"✅ **Días transcurridos:** {days_passed} días\n"
            f"⏳ **Días restantes:** {days_remaining} días"
        )
        
        embed4.add_field(
            name="📊 Línea de Tiempo",
            value=tiempo_text,
            inline=False
        )
        
        # Proyección
        if days_passed > 0:
            rate_per_day = total_games / days_passed
            projected_total = round(rate_per_day * days_total)
            
            projection_text = (
                f"📈 **Ritmo actual:** {round(rate_per_day, 2)} juegos/día\n"
                f"🎯 **Proyección final:** ~{projected_total} juegos totales\n"
                f"💡 **Por persona:** ~{round(projected_total / len(ranked_users), 1)} juegos c/u"
            )
            
            embed4.add_field(
                name="🔮 Proyección",
                value=projection_text,
                inline=False
            )
        
        # Footer con última actualización
        embed4.set_footer(text=f"Última actualización: {now.strftime('%d/%m/%Y %H:%M')}")
        
        # Enviar todos los embeds
        await interaction.followup.send(embeds=[embed1, embed2, embed3, embed4])


async def setup(bot):
    await bot.add_cog(Ranking(bot))