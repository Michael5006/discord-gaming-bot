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
    
    @app_commands.command(name="ranking", description="Ver el ranking interactivo del concurso")
    async def ranking(self, interaction: discord.Interaction):
        """Muestra el ranking con pestañas interactivas"""
        
        try:
            await interaction.response.defer()
            
            print("🔍 [RANKING] Obteniendo usuarios...")
            
            # Obtener usuarios y juegos
            users = await User.get_all_ranked()
            ranked_users = [user for user in users if user.total_games > 0]
            
            print(f"✅ [RANKING] Usuarios encontrados: {len(ranked_users)}")
            
            if not ranked_users:
                embed = discord.Embed(
                    title=f"{config.EMOJIS['ranking']} Ranking del Concurso",
                    description="Aún no hay participantes con juegos aprobados.",
                    color=config.COLORES['info']
                )
                await interaction.followup.send(embed=embed)
                return
            
            print("🔍 [RANKING] Obteniendo juegos...")
            
            # Obtener todos los juegos aprobados
            all_games = []
            for user in ranked_users:
                games = await Game.get_by_user(user.discord_id, status='APPROVED')
                all_games.extend(games)
            
            print(f"✅ [RANKING] Juegos encontrados: {len(all_games)}")
            print("🔍 [RANKING] Creando vista con pestañas...")
            
            # Crear vista con pestañas
            from views.ranking_view import RankingTabView
            
            view = RankingTabView(ranked_users, all_games)
            
            print("🔍 [RANKING] Generando embed...")
            embed = view.get_embed()
            
            print("🔍 [RANKING] Enviando mensaje...")
            await interaction.followup.send(
                embed=embed,
                view=view
            )
            
            print("✅ [RANKING] Comando completado exitosamente")
            
        except Exception as e:
            print(f"❌ [RANKING] Error: {e}")
            import traceback
            traceback.print_exc()
            
            error_embed = discord.Embed(
                title="❌ Error en Ranking",
                description=f"Hubo un error al cargar el ranking.\n\n```{str(e)[:1000]}```",
                color=config.COLORES['rechazado']
            )
            
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except:
                pass
    
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
        """Dashboard interactivo con menú desplegable"""
        
        try:
            await interaction.response.defer()
            
            print("🔍 [TABLERO] Obteniendo datos...")
            
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
            
            # Obtener todos los juegos
            all_games = []
            for user in ranked_users:
                games = await Game.get_by_user(user.discord_id, status='APPROVED')
                all_games.extend(games)
            
            print(f"✅ [TABLERO] {len(ranked_users)} usuarios, {len(all_games)} juegos")
            
            # Crear vista con select menu
            from views.dashboard_view import DashboardView, RefreshButton
            
            view = DashboardView(ranked_users, all_games)
            view.add_item(RefreshButton())  # Agregar botón de actualizar
            
            await interaction.followup.send(
                embed=view.get_main_embed(),
                view=view
            )
            
            print("✅ [TABLERO] Comando completado")
            
        except Exception as e:
            print(f"❌ [TABLERO] Error: {e}")
            import traceback
            traceback.print_exc()
            
            error_embed = discord.Embed(
                title="❌ Error en Tablero",
                description=f"Hubo un error al cargar el dashboard.\n\n```{str(e)[:1000]}```",
                color=config.COLORES['rechazado']
            )
            
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except:
                pass
        
    @ranking.error
    @mi_posicion.error
    @estadisticas.error
    @tablero.error
    async def ranking_error(self, interaction: discord.Interaction, error):
        """Maneja errores de comandos de ranking"""
        print(f"❌ [RANKING ERROR] {error}")
        import traceback
        traceback.print_exc()
        
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al ejecutar el comando.",
            color=config.COLORES['rechazado']
        )
        
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                pass


async def setup(bot):
    await bot.add_cog(Ranking(bot))