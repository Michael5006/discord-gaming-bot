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
    @app_commands.describe(juego="Juego a aprobar")
    @app_commands.check(is_admin)
    async def aprobar(self, interaction: discord.Interaction, juego: str):
        """Aprueba un juego pendiente"""
        
        # El parámetro 'juego' viene como "ID:Usuario - Nombre del Juego"
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
        
        game = await Game.get_by_id(game_id)
        
        if not game:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description=f"No se encontró el juego.",
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
        
        # Aprobar el juego
        success = await Game.approve(game_id, interaction.user.id)
        
        if success:
            # Actualizar estadísticas del usuario
            await User.update_stats(game.discord_user_id)
            
            # Obtener usuario actualizado
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
            
            # Intentar notificar al usuario
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
    
    @aprobar.autocomplete('juego')
    async def aprobar_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado para juegos pendientes"""
        
        # Obtener todos los juegos pendientes
        games = await Game.get_pending()
        
        if not games:
            return [app_commands.Choice(name="No hay juegos pendientes", value="0:ninguno")]
        
        # Filtrar por lo que el usuario está escribiendo
        filtered_games = [
            game for game in games
            if current.lower() in game.game_name.lower() or current.lower() in game.username.lower()
        ][:25]
        
        # Crear opciones con formato "ID:Usuario - Nombre - Categoría (Puntos)"
        choices = []
        for game in filtered_games:
            platino_text = " 🏆" if game.has_platinum else ""
            recomp_text = " 🔄" if game.is_recompleted else ""
            choice_name = f"{game.username} - {game.game_name}{platino_text}{recomp_text} - {game.category} ({game.total_points}pts)"
            choice_value = f"{game.id}:{game.username} - {game.game_name}"
            choices.append(app_commands.Choice(name=choice_name[:100], value=choice_value[:100]))
        
        return choices
    
    @app_commands.command(name="rechazar", description="[ADMIN] Rechazar un juego")
    @app_commands.describe(
        juego="Juego a rechazar",
        razon="Razón del rechazo"
    )
    @app_commands.check(is_admin)
    async def rechazar(self, interaction: discord.Interaction, juego: str, razon: str):
        """Rechaza un juego pendiente"""
        
        # El parámetro 'juego' viene como "ID:Usuario - Nombre del Juego"
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
        
        game = await Game.get_by_id(game_id)
        
        if not game:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description=f"No se encontró el juego.",
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
        
        # Rechazar el juego
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
            
            # Intentar notificar al usuario
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
    
    @rechazar.autocomplete('juego')
    async def rechazar_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado para juegos pendientes"""
        
        # Obtener todos los juegos pendientes
        games = await Game.get_pending()
        
        if not games:
            return [app_commands.Choice(name="No hay juegos pendientes", value="0:ninguno")]
        
        # Filtrar por lo que el usuario está escribiendo
        filtered_games = [
            game for game in games
            if current.lower() in game.game_name.lower() or current.lower() in game.username.lower()
        ][:25]
        
        # Crear opciones con formato "ID:Usuario - Nombre - Categoría (Puntos)"
        choices = []
        for game in filtered_games:
            platino_text = " 🏆" if game.has_platinum else ""
            recomp_text = " 🔄" if game.is_recompleted else ""
            choice_name = f"{game.username} - {game.game_name}{platino_text}{recomp_text} - {game.category} ({game.total_points}pts)"
            choice_value = f"{game.id}:{game.username} - {game.game_name}"
            choices.append(app_commands.Choice(name=choice_name[:100], value=choice_value[:100]))
        
        return choices
    
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
            
     ## EDITAR JUEGO ##       
    @app_commands.command(name="editar-juego", description="[ADMIN] Editar un juego aprobado")
    @app_commands.describe(
        usuario="Usuario dueño del juego",
        juego="Juego a editar",
        nombre="Nuevo nombre del juego (opcional)",
        categoria="Nueva categoría (opcional)",
        plataforma="Nueva plataforma (opcional)",
        platino="¿Tiene platino? (opcional)",
        recompletado="¿Es re-completado? (opcional)"
    )
    @app_commands.choices(categoria=[
        app_commands.Choice(name=f"{config.EMOJIS['retro']} Retro (1 punto)", value="Retro"),
        app_commands.Choice(name=f"{config.EMOJIS['indie']} Indie (1 punto)", value="Indie"),
        app_commands.Choice(name=f"{config.EMOJIS['aa']} AA (2 puntos)", value="Aa"),
        app_commands.Choice(name=f"{config.EMOJIS['aaa']} AAA (3 puntos)", value="Aaa"),
    ])
    @app_commands.choices(plataforma=[
        app_commands.Choice(name=f"{config.EMOJIS['ps5']} PlayStation 5", value="PS5"),
        app_commands.Choice(name=f"{config.EMOJIS['steam']} Steam", value="Steam"),
    ])
    @app_commands.choices(platino=[
        app_commands.Choice(name=f"{config.EMOJIS['platino']} Sí", value="si"),
        app_commands.Choice(name="❌ No", value="no"),
    ])
    @app_commands.choices(recompletado=[
        app_commands.Choice(name="🆕 No", value="no"),
        app_commands.Choice(name="🔄 Sí", value="si"),
    ])
    @app_commands.check(is_admin)
    async def editar_juego(
        self,
        interaction: discord.Interaction,
        usuario: discord.User,
        juego: str,
        nombre: str = None,
        categoria: app_commands.Choice[str] = None,
        plataforma: app_commands.Choice[str] = None,
        platino: app_commands.Choice[str] = None,
        recompletado: app_commands.Choice[str] = None
    ):
        """Edita un juego ya registrado"""
        
        # El parámetro 'juego' vendrá como "ID:Nombre del Juego"
        # Extraer el ID
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
                description=f"No se encontró el juego.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Verificar que el juego pertenece al usuario seleccionado
        if game.discord_user_id != usuario.id:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description=f"Este juego no pertenece a {usuario.name}.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Verificar si hay algo que editar
        if not any([nombre, categoria, plataforma, platino, recompletado]):
            embed = discord.Embed(
                title=f"{config.EMOJIS['advertencia']} Sin Cambios",
                description="No especificaste ningún campo para editar.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Guardar valores originales para mostrar
        cambios = []
        
        # Preparar valores nuevos (mantener los viejos si no se especifica)
        nuevo_nombre = nombre if nombre else game.game_name
        nueva_categoria = categoria.value if categoria else game.category
        nueva_plataforma = plataforma.value if plataforma else game.platform
        nuevo_platino = (platino.value == "si") if platino else game.has_platinum
        nuevo_recompletado = (recompletado.value == "si") if recompletado else game.is_recompleted
        
        # Registrar cambios
        if nombre and nombre != game.game_name:
            cambios.append(f"**Nombre:** {game.game_name} → {nombre}")
        
        if categoria and categoria.value != game.category:
            cambios.append(f"**Categoría:** {game.category} → {categoria.value}")
        
        if plataforma and plataforma.value != game.platform:
            cambios.append(f"**Plataforma:** {game.platform} → {plataforma.value}")
        
        if platino:
            nuevo_estado = "Sí" if platino.value == "si" else "No"
            viejo_estado = "Sí" if game.has_platinum else "No"
            if nuevo_estado != viejo_estado:
                cambios.append(f"**Platino:** {viejo_estado} → {nuevo_estado}")
        
        if recompletado:
            nuevo_estado = "Sí" if recompletado.value == "si" else "No"
            viejo_estado = "Sí" if game.is_recompleted else "No"
            if nuevo_estado != viejo_estado:
                cambios.append(f"**Re-completado:** {viejo_estado} → {nuevo_estado}")
        
        # Si no hay cambios reales
        if not cambios:
            embed = discord.Embed(
                title=f"{config.EMOJIS['info']} Sin Cambios",
                description="Los valores especificados son iguales a los actuales.",
                color=config.COLORES['info']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Recalcular puntos
        nuevos_puntos = config.PUNTOS_CATEGORIA[nueva_categoria.lower()]
        if nuevo_platino:
            nuevos_puntos += config.PUNTOS_CATEGORIA['platino']
        
        # Actualizar en la base de datos
        db = await get_db()
        try:
            await db.execute('''
                UPDATE games
                SET game_name = ?,
                    category = ?,
                    platform = ?,
                    has_platinum = ?,
                    is_recompleted = ?,
                    total_points = ?
                WHERE id = ?
            ''', (nuevo_nombre, nueva_categoria, nueva_plataforma, 
                  int(nuevo_platino), int(nuevo_recompletado), nuevos_puntos, game_id))
            await db.commit()
            
            # Actualizar estadísticas del usuario
            await User.update_stats(game.discord_user_id)
            
            # Obtener usuario actualizado
            user = await User.get(game.discord_user_id)
            
            # Embed de confirmación
            embed = discord.Embed(
                title=f"{config.EMOJIS['editar']} Juego Editado",
                description=f"El juego **{nuevo_nombre}** ha sido modificado.",
                color=config.COLORES['aprobado']
            )
            
            embed.add_field(
                name="📝 Cambios Realizados",
                value="\n".join(cambios),
                inline=False
            )
            
            if game.total_points != nuevos_puntos:
                embed.add_field(
                    name=f"{config.EMOJIS['puntos']} Puntos",
                    value=f"{game.total_points} pts → **{nuevos_puntos} pts**",
                    inline=True
                )
            
            embed.add_field(
                name=f"{config.EMOJIS['usuario']} Usuario: {usuario.name}",
                value=f"Puntos totales: **{user.total_points}** pts ({user.total_games} juegos)",
                inline=False
            )
            
            embed.set_footer(text=f"Editado por {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed)
            
            # Notificar al usuario
            try:
                notif_embed = discord.Embed(
                    title=f"{config.EMOJIS['editar']} Tu Juego Fue Editado",
                    description=f"Un admin modificó tu juego **{nuevo_nombre}**.",
                    color=config.COLORES['info']
                )
                notif_embed.add_field(
                    name="Cambios",
                    value="\n".join(cambios),
                    inline=False
                )
                notif_embed.add_field(
                    name="Puntos Actuales",
                    value=f"Ahora tienes **{user.total_points}** pts totales",
                    inline=False
                )
                await usuario.send(embed=notif_embed)
            except:
                pass
            
        finally:
            await db.close()
    
    @editar_juego.autocomplete('juego')
    async def juego_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado dinámico para mostrar juegos del usuario seleccionado"""
        
        # Obtener el usuario que se seleccionó en el comando
        usuario = interaction.namespace.usuario
        
        if not usuario:
            return []
        
        # Obtener todos los juegos del usuario
        games = await Game.get_by_user(usuario.id, status='APPROVED')
        
        if not games:
            return [app_commands.Choice(name="Este usuario no tiene juegos", value="0:ninguno")]
        
        # Filtrar por lo que el usuario está escribiendo
        filtered_games = [
            game for game in games
            if current.lower() in game.game_name.lower()
        ][:25]  # Discord limita a 25 opciones
        
        # Crear opciones con formato "ID:Nombre - Categoría (Puntos)"
        choices = []
        for game in filtered_games:
            platino_text = " 🏆" if game.has_platinum else ""
            choice_name = f"{game.game_name}{platino_text} - {game.category} ({game.total_points}pts)"
            choice_value = f"{game.id}:{game.game_name}"
            choices.append(app_commands.Choice(name=choice_name[:100], value=choice_value[:100]))
        
        return choices 
    
    @app_commands.command(name="eliminar-juego", description="[ADMIN] Eliminar cualquier juego del sistema")
    @app_commands.describe(
        usuario="Usuario dueño del juego",
        juego="Juego a eliminar"
    )
    @app_commands.check(is_admin)
    async def eliminar_juego(self, interaction: discord.Interaction, usuario: discord.User, juego: str):
        """Permite a un admin eliminar cualquier juego"""
        
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
        
        # Verificar que pertenece al usuario seleccionado
        if game.discord_user_id != usuario.id:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description=f"Este juego no pertenece a {usuario.name}.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Guardar info antes de eliminar
        game_name = game.game_name
        game_status = game.status
        game_points = game.total_points
        user_id = game.discord_user_id
        
        # Eliminar el juego
        db = await get_db()
        try:
            await db.execute('DELETE FROM games WHERE id = ?', (game_id,))
            await db.commit()
            
            # Si era aprobado, actualizar stats del usuario
            if game_status == 'APPROVED':
                await User.update_stats(user_id)
                user = await User.get(user_id)
                stats_text = f"\n\n**Stats actualizadas de {usuario.name}:**\nPuntos totales: {user.total_points} pts ({user.total_games} juegos)"
            else:
                stats_text = ""
            
            embed = discord.Embed(
                title=f"{config.EMOJIS['eliminar']} Juego Eliminado",
                description=f"**{game_name}** ha sido eliminado del sistema.",
                color=config.COLORES['aprobado']
            )
            
            status_emoji = {
                'PENDING': '⏳ Pendiente',
                'APPROVED': '✅ Aprobado',
                'REJECTED': '❌ Rechazado'
            }.get(game_status, game_status)
            
            embed.add_field(
                name="Información del Juego Eliminado",
                value=(
                    f"**Juego:** {game_name}\n"
                    f"**Usuario:** {usuario.name}\n"
                    f"**Estado:** {status_emoji}\n"
                    f"**Puntos:** {game_points} pts"
                    f"{stats_text}"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Eliminado por {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed)
            
            # Notificar al usuario
            try:
                notif_embed = discord.Embed(
                    title=f"{config.EMOJIS['advertencia']} Tu Juego Fue Eliminado",
                    description=f"Un admin eliminó tu juego **{game_name}**.",
                    color=config.COLORES['info']
                )
                notif_embed.add_field(
                    name="Estado del juego",
                    value=status_emoji,
                    inline=False
                )
                if game_status == 'APPROVED':
                    notif_embed.add_field(
                        name="Tus puntos actuales",
                        value=f"{user.total_points} pts ({user.total_games} juegos)",
                        inline=False
                    )
                await usuario.send(embed=notif_embed)
            except:
                pass
            
        except Exception as e:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description="Hubo un error al eliminar el juego.",
                color=config.COLORES['rechazado']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        finally:
            await db.close()
    
    @eliminar_juego.autocomplete('juego')
    async def eliminar_juego_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado para juegos del usuario seleccionado"""
        
        # Obtener el usuario seleccionado
        usuario = interaction.namespace.usuario
        
        if not usuario:
            return []
        
        # Obtener todos los juegos del usuario (pendientes y aprobados)
        pending_games = await Game.get_by_user(usuario.id, status='PENDING')
        approved_games = await Game.get_by_user(usuario.id, status='APPROVED')
        all_games = pending_games + approved_games
        
        if not all_games:
            return [app_commands.Choice(name="Este usuario no tiene juegos", value="0:ninguno")]
        
        # Filtrar por lo que está escribiendo
        filtered_games = [
            game for game in all_games
            if current.lower() in game.game_name.lower()
        ][:25]
        
        # Crear opciones
        choices = []
        for game in filtered_games:
            status_emoji = {
                'PENDING': '⏳',
                'APPROVED': '✅',
                'REJECTED': '❌'
            }.get(game.status, '')
            
            platino_text = " 🏆" if game.has_platinum else ""
            recomp_text = " 🔄" if game.is_recompleted else ""
            
            choice_name = f"{status_emoji} {game.game_name}{platino_text}{recomp_text} - {game.category} ({game.total_points}pts)"
            choice_value = f"{game.id}:{game.game_name}"
            choices.append(app_commands.Choice(name=choice_name[:100], value=choice_value[:100]))
        
        return choices
    
    @pendientes.error
    @revisar.error
    @aprobar.error
    @rechazar.error
    @marcar_elkie.error
    @editar_juego.error
    @eliminar_juego.error
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