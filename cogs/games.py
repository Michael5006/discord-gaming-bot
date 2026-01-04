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
        nombre="Busca el juego por nombre",
        plataforma="Plataforma en la que lo jugaste",
        platino="¿Obtuviste el platino/100%?",
        recompletado="¿Es un juego que ya habías completado antes?"
    )
    @app_commands.choices(plataforma=[
        app_commands.Choice(name=f"{config.EMOJIS['ps5']} PlayStation 5", value="PS5"),
        app_commands.Choice(name=f"{config.EMOJIS['steam']} Steam", value="Steam"),
    ])
    @app_commands.choices(platino=[
        app_commands.Choice(name=f"{config.EMOJIS['platino']} Sí", value="si"),
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
        plataforma: app_commands.Choice[str],
        platino: app_commands.Choice[str],
        recompletado: app_commands.Choice[str]
    ):
        """Registra un juego completado usando la base de datos de RAWG"""
        
        await interaction.response.defer(ephemeral=True)
        
        # El parámetro 'nombre' viene como "ID:Nombre del Juego"
        try:
            parts = nombre.split(':', 1)
            if len(parts) == 2 and parts[0].isdigit():
                game_id = int(parts[0])
                game_name = parts[1]
            else:
                # Permitir registro manual si no viene de RAWG
                game_id = None
                game_name = nombre
        except:
            game_id = None
            game_name = nombre
        
        # Si viene de RAWG, obtener detalles completos
        if game_id:
            from utils.rawg_api import rawg_client
            game_data = rawg_client.get_game_details(game_id)
            
            if not game_data:
                embed = discord.Embed(
                    title=f"{config.EMOJIS['error']} Error",
                    description="No se pudo obtener información del juego.",
                    color=config.COLORES['rechazado']
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Extraer información
            nombre_oficial = game_data.get('name', game_name)
            year = game_data.get('released', '').split('-')[0] if game_data.get('released') else 'Unknown'
            
            # Obtener plataformas
            platforms_data = game_data.get('platforms', [])
            available_platforms = []
            for p in platforms_data:
                platform_info = p.get('platform', {})
                platform_name = platform_info.get('name', '')
                if 'PlayStation 5' in platform_name or 'PlayStation 4' in platform_name:
                    available_platforms.append('PS5')
                elif 'PC' in platform_name:
                    available_platforms.append('Steam')
            
            # Validar que el juego esté en la plataforma seleccionada
            selected_platform = plataforma.value
            if selected_platform not in available_platforms:
                # Si seleccionó PS5 pero solo está en PS4, permitirlo
                if selected_platform == 'PS5' and 'PS4' not in [p.get('platform', {}).get('name', '') for p in platforms_data]:
                    embed = discord.Embed(
                        title=f"{config.EMOJIS['advertencia']} Plataforma No Disponible",
                        description=f"**{nombre_oficial}** no está disponible en **{selected_platform}**.",
                        color=config.COLORES['rechazado']
                    )
                    embed.add_field(
                        name="Plataformas Disponibles",
                        value=", ".join(available_platforms) if available_platforms else "No disponible en PS5/Steam",
                        inline=False
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            
            # Detectar categoría automáticamente
            metacritic = game_data.get('metacritic', 0)
            categoria_detectada = rawg_client._detect_category(game_data, year, metacritic)
            
            # Convertir a formato de la BD
            categoria_map = {
                'Retro': 'Retro',
                'Indie': 'Indie',
                'Aa': 'AA',
                'Aaa': 'AAA'
            }
            categoria_nombre = categoria_map.get(categoria_detectada, 'AA')
            
            # Imagen del juego
            game_image = game_data.get('background_image', '')
            
        else:
            # Registro manual (fallback si no viene de RAWG)
            nombre_oficial = game_name
            year = 'Unknown'
            categoria_nombre = 'AA'  # Default
            game_image = ''
        
        # Crear/obtener usuario
        await User.get_or_create(interaction.user.id, interaction.user.name)
        
        # Verificar si ya tiene este juego aprobado (para detectar re-completado)
        existing_games = await Game.get_by_user(interaction.user.id, status='APPROVED')
        is_recompletado = recompletado.value == "si"
        
        # Auto-detectar re-completado
        for existing_game in existing_games:
            if existing_game.game_name.lower() == nombre_oficial.lower():
                if recompletado.value == "no":
                    # Preguntar si quiere marcarlo como re-completado
                    is_recompletado = True
                break
        
        # Calcular puntos
        puntos_categoria = config.PUNTOS_CATEGORIA[categoria_nombre.lower()]
        puntos_platino = config.PUNTOS_CATEGORIA['platino'] if platino.value == "si" else 0
        puntos_totales = puntos_categoria + puntos_platino
        
        # Registrar el juego
        has_platinum = platino.value == "si"
        success = await Game.create(
            discord_user_id=interaction.user.id,
            username=interaction.user.name,
            game_name=nombre_oficial,
            category=categoria_nombre,
            platform=plataforma.value,
            has_platinum=has_platinum,
            is_recompleted=is_recompletado
        )
        
        if success:
            # Embed de confirmación
            embed = discord.Embed(
                title=f"{config.EMOJIS['exito']} ¡Juego Registrado!",
                description=f"**{nombre_oficial}** ha sido registrado exitosamente.",
                color=config.COLORES['aprobado']
            )
            
            if game_image:
                embed.set_thumbnail(url=game_image)
            
            # Información del juego
            categoria_emoji = config.EMOJIS.get(categoria_nombre.lower(), '🎮')
            
            info_text = f"{categoria_emoji} **Categoría:** {categoria_nombre}"
            if year and year != 'Unknown':
                info_text += f" ({year})"
            info_text += f"\n🎮 **Plataforma:** {plataforma.value}"
            
            if has_platinum:
                info_text += f"\n{config.EMOJIS['platino']} **Platino:** Sí"
            
            if is_recompletado:
                info_text += f"\n🔄 **Re-completado:** Sí"
            
            embed.add_field(
                name="📋 Información",
                value=info_text,
                inline=False
            )
            
            embed.add_field(
                name=f"{config.EMOJIS['puntos']} Puntos",
                value=f"**{puntos_totales}** puntos ({puntos_categoria} + {puntos_platino})",
                inline=True
            )
            
            embed.add_field(
                name=f"{config.EMOJIS['pendiente']} Estado",
                value="Pendiente de aprobación",
                inline=True
            )
            
            embed.set_footer(text="Un admin revisará tu registro pronto")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title=f"{config.EMOJIS['error']} Error",
                description="Hubo un error al registrar el juego. Inténtalo de nuevo.",
                color=config.COLORES['rechazado']
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @registrar.autocomplete('nombre')
    async def nombre_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado dinámico de juegos desde RAWG"""
        
        # Necesita al menos 3 caracteres para buscar
        if len(current) < 3:
            return [
                app_commands.Choice(
                    name="Escribe al menos 3 letras para buscar...",
                    value="0:buscar"
                )
            ]
        
        # Buscar en RAWG
        from utils.rawg_api import rawg_client
        games = rawg_client.search_games(current, limit=40)
        
        if not games:
            return [
                app_commands.Choice(
                    name=f"No se encontraron juegos para '{current}'",
                    value=f"0:{current}"
                ),
                app_commands.Choice(
                    name="→ Registrar manualmente (escribe el nombre completo)",
                    value=f"manual:{current}"
                )
            ]
        
        # Formatear opciones
        choices = []
        for game in games:
            # Crear nombre descriptivo
            name_parts = [game['name']]
            
            if game['year'] and game['year'] != 'Unknown':
                name_parts.append(f"({game['year']})")
            
            # Agregar categoría detectada
            categoria_emoji = {
                'Retro': '🕹️',
                'Indie': '🎨',
                'Aa': '🎯',
                'Aaa': '👑'
            }.get(game['category'], '🎮')
            name_parts.append(f"{categoria_emoji}")
            
            # Plataformas
            platforms_str = ", ".join(game['platforms'][:2])  # Máximo 2 plataformas
            name_parts.append(f"[{platforms_str}]")
            
            choice_name = " ".join(name_parts)
            choice_value = f"{game['id']}:{game['name']}"
            
            choices.append(
                app_commands.Choice(
                    name=choice_name[:100],  # Discord limita a 100 caracteres
                    value=choice_value[:100]
                )
            )
        
        # Agregar opción de registro manual al final
        if len(choices) < 25:
            choices.append(
                app_commands.Choice(
                    name="→ No está en la lista - Registrar manualmente",
                    value=f"manual:{current}"
                )
            )
        
        return choices[:25]  # Discord limita a 25 opciones

async def setup(bot):
    await bot.add_cog(Games(bot))