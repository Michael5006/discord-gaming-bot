import discord
from discord import app_commands
from discord.ext import commands
import config
from models.game import Game
from models.user import User
from models.database import get_db

class Admin(commands.Cog):
    """Comandos de administración para gestionar el concurso"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def is_admin(interaction: discord.Interaction) -> bool:
        """Verifica si el usuario tiene permisos de administrador"""
        return interaction.user.guild_permissions.administrator
    
    @app_commands.command(name="pendientes", description="[ADMIN] Ver todos los juegos pendientes de aprobación")
    @app_commands.check(is_admin)
    async def pendientes(self, interaction: discord.Interaction):
        """Muestra todos los juegos pendientes de aprobación"""
        
        games = await Game.get_pending()
        
        if not games:
            embed = discord.Embed(
                title=f"{config.EMOJIS['info']} Juegos Pendientes",
                description="No hay juegos pendientes de aprobación.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"{config.EMOJIS['pendiente']} Juegos Pendientes de Aprobación",
            description=f"Hay **{len(games)}** juego(s) esperando revisión.",
            color=config.COLORES['pendiente']
        )
        
        for game in games[:10]:
            categoria_emoji = config.EMOJIS.get(game.category.lower(), '🎮')
            platino_text = f" {config.EMOJIS['platino']}" if game.has_platinum else ""
            recompletado_text = " 🔄" if game.is_recompleted else ""
            
            embed.add_field(
                name=f"ID: {game.id} • {game.game_name}{platino_text}{recompletado_text}",
                value=(
                    f"👤 **Usuario:** {game.username}\n"
                    f"{categoria_emoji} **Categoría:** {game.category}\n"
                    f"🎮 **Plataforma:** {game.platform}\n"
                    f"{config.EMOJIS['puntos']} **Puntos:** {game.total_points}\n"
                    f"{config.EMOJIS['fecha']} **Registrado:** {game.submission_date[:10]}"
                ),
                inline=False
            )
        
        if len(games) > 10:
            embed.set_footer(text=f"Mostrando 10 de {len(games)} juegos pendientes")
        else:
            embed.set_footer(text="Usa /revisar [id] para aprobar o rechazar un juego")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="revisar", description="[ADMIN] Revisar un juego específico")
    @app_commands.describe(game_id="ID del juego a revisar")
    @app_commands.check(is_admin)
    async def revisar(self, interaction: discord.Interaction, game_id: int):
        """Muestra los detalles de un juego y permite aprobarlo o rechazarlo"""
        
        game = await Game.get_by_id(game_id)
        
        if not game:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description=f"No se encontró ningún juego con ID **{game_id}**.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if game.status != 'PENDING':
            status_text = {
                'APPROVED': '✅ Aprobado',
                'REJECTED': '❌ Rechazado'
            }.get(game.status, game.status)
            
            embed = discord.Embed(
                title=f"{config.EMOJIS['advertencia']} Juego Ya Revisado",
                description=f"Este juego ya fue revisado.\n\n**Estado:** {status_text}",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        categoria_emoji = config.EMOJIS.get(game.category.lower(), '🎮')
        
        embed = discord.Embed(
            title=f"{config.EMOJIS['buscar']} Revisar Juego #{game.id}",
            description=f"**{game.game_name}**",
            color=config.COLORES['pendiente']
        )
        
        embed.add_field(
            name=f"{config.EMOJIS['usuario']} Usuario",
            value=game.username,
            inline=True
        )
        
        embed.add_field(
            name=f"{categoria_emoji} Categoría",
            value=game.category,
            inline=True
        )
        
        embed.add_field(
            name="🎮 Plataforma",
            value=game.platform,
            inline=True
        )
        
        embed.add_field(
            name=f"{config.EMOJIS['platino']} Platino",
            value="✅ Sí" if game.has_platinum else "❌ No",
            inline=True
        )
        
        if game.is_recompleted:
            embed.add_field(
                name="Tipo",
                value="🔄 Re-completado",
                inline=True
            )
        
        embed.add_field(
            name=f"{config.EMOJIS['puntos']} Puntos",
            value=f"**{game.total_points}** puntos",
            inline=True
        )
        
        embed.add_field(
            name=f"{config.EMOJIS['fecha']} Fecha de Registro",
            value=game.submission_date[:10],
            inline=False
        )
        
        if game.evidence_url:
            embed.add_field(
                name="📸 Evidencia",
                value=f"[Ver evidencia]({game.evidence_url})",
                inline=False
            )
        
        embed.set_footer(text=f"Usa /aprobar {game_id} o /rechazar {game_id}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="aprobar", description="[ADMIN] Aprobar un juego")
    @app_commands.describe(game_id="ID del juego a aprobar")
    @app_commands.check(is_admin)
    async def aprobar(self, interaction: discord.Interaction, game_id: int):
        """Aprueba un juego pendiente"""
        
        game = await Game.get_by_id(game_id)
        
        if not game:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description=f"No se encontró ningún juego con ID **{game_id}**.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if game.status != 'PENDING':
            embed = discord.Embed(
                title=f"{config.EMOJIS['advertencia']} Error",
                description="Este juego ya fue revisado anteriormente.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        success = await Game.approve(game_id, interaction.user.id)
        
        if success:
            await User.update_stats(game.discord_user_id)
            user = await User.get(game.discord_user_id)
            
            embed = discord.Embed(
                title=f"{config.EMOJIS['aprobar']} Juego Aprobado",
                description=f"**{game.game_name}** ha sido aprobado exitosamente.",
                color=config.COLORES['aprobado']
            )
            
            embed.add_field(
                name=f"{config.EMOJIS['usuario']} Usuario",
                value=game.username,
                inline=True
            )
            
            embed.add_field(
                name=f"{config.EMOJIS['puntos']} Puntos Otorgados",
                value=f"+{game.total_points} puntos",
                inline=True
            )
            
            embed.add_field(
                name=f"{config.EMOJIS['ranking']} Estadísticas Actualizadas",
                value=f"**Total:** {user.total_points} pts ({user.total_games} juegos)",
                inline=False
            )
            
            embed.set_footer(text=f"Aprobado por {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed)
            
            try:
                user_discord = await self.bot.fetch_user(game.discord_user_id)
                notif_embed = discord.Embed(
                    title=f"{config.EMOJIS['exito']} ¡Tu Juego Fue Aprobado!",
                    description=f"**{game.game_name}** ha sido aprobado.",
                    color=config.COLORES['aprobado']
                )
                notif_embed.add_field(
                    name=f"{config.EMOJIS['puntos']} Puntos",
                    value=f"+{game.total_points} puntos",
                    inline=True
                )
                notif_embed.add_field(
                    name="Total",
                    value=f"{user.total_points} pts",
                    inline=True
                )
                await user_discord.send(embed=notif_embed)
            except:
                pass
        else:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description="Hubo un error al aprobar el juego.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="rechazar", description="[ADMIN] Rechazar un juego")
    @app_commands.describe(
        game_id="ID del juego a rechazar",
        razon="Razón del rechazo"
    )
    @app_commands.check(is_admin)
    async def rechazar(self, interaction: discord.Interaction, game_id: int, razon: str):
        """Rechaza un juego pendiente"""
        
        game = await Game.get_by_id(game_id)
        
        if not game:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description=f"No se encontró ningún juego con ID **{game_id}**.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if game.status != 'PENDING':
            embed = discord.Embed(
                title=f"{config.EMOJIS['advertencia']} Error",
                description="Este juego ya fue revisado anteriormente.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        success = await Game.reject(game_id, interaction.user.id, razon)
        
        if success:
            embed = discord.Embed(
                title=f"{config.EMOJIS['rechazar']} Juego Rechazado",
                description=f"**{game.game_name}** ha sido rechazado.",
                color=config.COLORES['rechazado']
            )
            
            embed.add_field(
                name=f"{config.EMOJIS['usuario']} Usuario",
                value=game.username,
                inline=True
            )
            
            embed.add_field(
                name="Razón",
                value=razon,
                inline=False
            )
            
            embed.set_footer(text=f"Rechazado por {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed)
            
            try:
                user_discord = await self.bot.fetch_user(game.discord_user_id)
                notif_embed = discord.Embed(
                    title=f"{config.EMOJIS['rechazar']} Tu Juego Fue Rechazado",
                    description=f"**{game.game_name}** no fue aprobado.",
                    color=config.COLORES['rechazado']
                )
                notif_embed.add_field(
                    name="Razón",
                    value=razon,
                    inline=False
                )
                notif_embed.set_footer(text="Puedes registrar otro juego si cumple las reglas")
                await user_discord.send(embed=notif_embed)
            except:
                pass
        else:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description="Hubo un error al rechazar el juego.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="marcar-elkie", description="[ADMIN] Marcar o desmarcar a un usuario como Elkie")
    @app_commands.describe(usuario="Usuario a marcar/desmarcar como Elkie")
    @app_commands.check(is_admin)
    async def marcar_elkie(self, interaction: discord.Interaction, usuario: discord.User):
        """Marca o desmarca a un usuario como Elkie"""
        
        user = await User.get(usuario.id)
        if not user:
            await User.create(usuario.id, usuario.name)
            user = await User.get(usuario.id)
        
        db = await get_db()
        try:
            if user.is_elkie:
                await db.execute('UPDATE users SET is_elkie = 0 WHERE discord_id = ?', (usuario.id,))
                await db.commit()
                
                embed = discord.Embed(
                    title=f"{config.EMOJIS['config']} Elkie Desmarcado",
                    description=f"**{usuario.name}** ya no es Elkie.\nLa regla especial de premios ya no aplica.",
                    color=config.COLORES['info']
                )
            else:
                await db.execute('UPDATE users SET is_elkie = 0')
                await db.execute('UPDATE users SET is_elkie = 1 WHERE discord_id = ?', (usuario.id,))
                await db.commit()
                
                embed = discord.Embed(
                    title=f"{config.EMOJIS['config']} Elkie Marcado",
                    description=f"**{usuario.name}** 👑 ahora es Elkie.\n\n**Regla especial activa:**\nSi Elkie gana, el 2do lugar recibirá premio de $20 USD.",
                    color=config.COLORES['info']
                )
            
            await interaction.response.send_message(embed=embed)
        finally:
            await db.close()
    
    @pendientes.error
    @revisar.error
    @aprobar.error
    @rechazar.error
    @marcar_elkie.error
    async def admin_error(self, interaction: discord.Interaction, error):
        """Maneja errores de permisos de admin"""
        if isinstance(error, app_commands.CheckFailure):
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Sin Permisos",
                description="No tienes permisos de administrador para usar este comando.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
async def setup(bot):
    await bot.add_cog(Admin(bot))