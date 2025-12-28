import discord
from discord import app_commands
from discord.ext import commands
import config
from models.game import Game
from models.user import User

class Games(commands.Cog):
    """Comandos relacionados con el registro y gestión de juegos"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="registrar", description="Registrar un juego completado")
    @app_commands.describe(
        nombre="Nombre del juego",
        categoria="Categoría del juego",
        plataforma="Plataforma donde lo jugaste",
        platino="¿Obtuviste el platino/100%?",
        recompletado="¿Es un juego que ya habías completado antes?"
    )
    @app_commands.choices(categoria=[
        app_commands.Choice(name=f"{config.EMOJIS['retro']} Retro (1 punto)", value="retro"),
        app_commands.Choice(name=f"{config.EMOJIS['indie']} Indie (1 punto)", value="indie"),
        app_commands.Choice(name=f"{config.EMOJIS['aa']} AA (2 puntos)", value="aa"),
        app_commands.Choice(name=f"{config.EMOJIS['aaa']} AAA (3 puntos)", value="aaa"),
    ])
    @app_commands.choices(plataforma=[
        app_commands.Choice(name=f"{config.EMOJIS['ps5']} PlayStation 5", value="PS5"),
        app_commands.Choice(name=f"{config.EMOJIS['steam']} Steam", value="Steam"),
    ])
    @app_commands.choices(platino=[
        app_commands.Choice(name=f"{config.EMOJIS['platino']} Sí (+1 punto)", value="si"),
        app_commands.Choice(name="❌ No", value="no"),
    ])
    @app_commands.choices(recompletado=[
        app_commands.Choice(name="🆕 No, es primera vez", value="no"),
        app_commands.Choice(name="🔄 Sí, lo re-completé", value="si"),
    ])
    async def registrar(
        self, 
        interaction: discord.Interaction,
        nombre: str,
        categoria: app_commands.Choice[str],
        plataforma: app_commands.Choice[str],
        platino: app_commands.Choice[str],
        recompletado: app_commands.Choice[str]
    ):
        """Registra un nuevo juego completado"""
        
        # Crear/obtener usuario
        await User.get_or_create(interaction.user.id, interaction.user.name)
        
        # Convertir valores
        has_platinum = (platino.value == "si")
        is_recompleted = (recompletado.value == "si")
        
        # Calcular puntos
        points = config.PUNTOS_CATEGORIA[categoria.value]
        if has_platinum:
            points += config.PUNTOS_CATEGORIA['platino']
        
        # Crear el juego en la BD
        success = await Game.create(
            discord_user_id=interaction.user.id,
            username=interaction.user.name,
            game_name=nombre,
            category=categoria.value.capitalize(),
            platform=plataforma.value,
            has_platinum=has_platinum,
            is_recompleted=is_recompleted
        )
        
        if success:
            # Crear embed de confirmación
            embed = discord.Embed(
                title=f"{config.EMOJIS['exito']} ¡Juego Registrado!",
                description=f"Tu juego ha sido enviado para aprobación.",
                color=config.COLORES['pendiente']
            )
            
            embed.add_field(
                name=f"{config.EMOJIS['registrar']} Juego",
                value=f"**{nombre}**",
                inline=False
            )
            
            # Info del juego
            categoria_emoji = config.EMOJIS.get(categoria.value, '🎮')
            embed.add_field(
                name="Categoría",
                value=f"{categoria_emoji} {categoria.value.capitalize()}",
                inline=True
            )
            
            embed.add_field(
                name="Plataforma",
                value=f"{config.EMOJIS.get(plataforma.value.lower(), '🎮')} {plataforma.value}",
                inline=True
            )
            
            embed.add_field(
                name="Platino",
                value=f"{config.EMOJIS['platino'] if has_platinum else '❌'} {'Sí' if has_platinum else 'No'}",
                inline=True
            )
            
            if is_recompleted:
                embed.add_field(
                    name="Tipo",
                    value="🔄 Re-completado",
                    inline=True
                )
            
            embed.add_field(
                name=f"{config.EMOJIS['puntos']} Puntos",
                value=f"**{points}** puntos",
                inline=True
            )
            
            embed.add_field(
                name=f"{config.EMOJIS['pendiente']} Estado",
                value="⏳ **Pendiente de aprobación**",
                inline=False
            )
            
            embed.set_footer(text="Un administrador revisará tu solicitud pronto")
            
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description="Hubo un error al registrar el juego. Intenta nuevamente.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="mis-juegos", description="Ver tus juegos aprobados")
    async def mis_juegos(self, interaction: discord.Interaction):
        """Muestra los juegos aprobados del usuario"""
        
        # Obtener juegos aprobados
        games = await Game.get_by_user(interaction.user.id, status='APPROVED')
        
        if not games:
            embed = discord.Embed(
                title=f"{config.EMOJIS['info']} Mis Juegos",
                description="Aún no tienes juegos aprobados.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Obtener stats del usuario
        user = await User.get(interaction.user.id)
        
        embed = discord.Embed(
            title=f"{config.EMOJIS['registrar']} Mis Juegos Aprobados",
            description=f"Total de juegos: **{len(games)}**\nPuntos totales: **{user.total_points}** {config.EMOJIS['puntos']}",
            color=config.COLORES['aprobado']
        )
        
        # Mostrar hasta 10 juegos
        for i, game in enumerate(games[:10], 1):
            categoria_emoji = config.EMOJIS.get(game.category.lower(), '🎮')
            platino_text = f" {config.EMOJIS['platino']}" if game.has_platinum else ""
            recompletado_text = " 🔄" if game.is_recompleted else ""
            
            embed.add_field(
                name=f"{i}. {game.game_name}{platino_text}{recompletado_text}",
                value=f"{categoria_emoji} {game.category} • {game.platform} • {game.total_points} pts\n`ID: {game.id}`",
                inline=False
            )
        
        if len(games) > 10:
            embed.set_footer(text=f"Mostrando 10 de {len(games)} juegos")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="mis-pendientes", description="Ver tus juegos pendientes de aprobación")
    async def mis_pendientes(self, interaction: discord.Interaction):
        """Muestra los juegos pendientes del usuario"""
        
        # Obtener juegos pendientes
        games = await Game.get_by_user(interaction.user.id, status='PENDING')
        
        if not games:
            embed = discord.Embed(
                title=f"{config.EMOJIS['info']} Juegos Pendientes",
                description="No tienes juegos pendientes de aprobación.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"{config.EMOJIS['pendiente']} Mis Juegos Pendientes",
            description=f"Tienes **{len(games)}** juego(s) esperando aprobación.",
            color=config.COLORES['pendiente']
        )
        
        for i, game in enumerate(games, 1):
            categoria_emoji = config.EMOJIS.get(game.category.lower(), '🎮')
            platino_text = f" {config.EMOJIS['platino']}" if game.has_platinum else ""
            
            embed.add_field(
                name=f"{i}. {game.game_name}{platino_text}",
                value=f"{categoria_emoji} {game.category} • {game.platform} • {game.total_points} pts",
                inline=False
            )
        
        embed.set_footer(text="Los admins revisarán tus juegos pronto")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(name="eliminar-pendiente", description="Eliminar uno de tus juegos pendientes")
    @app_commands.describe(juego="Juego pendiente a eliminar")
    async def eliminar_pendiente(self, interaction: discord.Interaction, juego: str):
        """Permite a un usuario eliminar sus propios juegos pendientes"""
        
        # El parámetro 'juego' viene como "ID:Nombre del Juego"
        try:
            game_id = int(juego.split(':')[0])
        except:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description="Error al procesar el juego seleccionado.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Obtener el juego
        game = await Game.get_by_id(game_id)
        
        if not game:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description="No se encontró el juego.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Verificar que sea del usuario
        if game.discord_user_id != interaction.user.id:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Sin Permisos",
                description="Solo puedes eliminar tus propios juegos.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Verificar que esté pendiente
        if game.status != 'PENDING':
            embed = discord.Embed(
                title=f"{config.EMOJIS['advertencia']} No Disponible",
                description="Solo puedes eliminar juegos que estén pendientes de aprobación.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Eliminar el juego
        from models.database import get_db
        db = await get_db()
        try:
            await db.execute('DELETE FROM games WHERE id = ?', (game_id,))
            await db.commit()
            
            embed = discord.Embed(
                title=f"{config.EMOJIS['eliminar']} Juego Eliminado",
                description=f"**{game.game_name}** ha sido eliminado de tus pendientes.",
                color=config.COLORES['aprobado']
            )
            
            embed.add_field(
                name="Juego Eliminado",
                value=f"{game.game_name} - {game.category} ({game.total_points} pts)",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description="Hubo un error al eliminar el juego.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        finally:
            await db.close()
    
    @eliminar_pendiente.autocomplete('juego')
    async def eliminar_pendiente_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado para juegos pendientes del usuario"""
        
        # Obtener juegos pendientes del usuario
        games = await Game.get_by_user(interaction.user.id, status='PENDING')
        
        if not games:
            return [app_commands.Choice(name="No tienes juegos pendientes", value="0:ninguno")]
        
        # Filtrar por lo que está escribiendo
        filtered_games = [
            game for game in games
            if current.lower() in game.game_name.lower()
        ][:25]
        
        # Crear opciones
        choices = []
        for game in filtered_games:
            platino_text = " 🏆" if game.has_platinum else ""
            recomp_text = " 🔄" if game.is_recompleted else ""
            choice_name = f"{game.game_name}{platino_text}{recomp_text} - {game.category} ({game.total_points}pts)"
            choice_value = f"{game.id}:{game.game_name}"
            choices.append(app_commands.Choice(name=choice_name[:100], value=choice_value[:100]))
        
        return choices

async def setup(bot):
    await bot.add_cog(Games(bot))