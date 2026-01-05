import discord
from discord import app_commands
from discord.ext import commands
import config

class Utils(commands.Cog):
    """Comandos de utilidad e información"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="reglas", description="Ver las reglas del concurso")
    async def reglas(self, interaction: discord.Interaction):
        """Muestra las reglas completas del concurso"""
        
        embed = discord.Embed(
            title=f"{config.EMOJIS['info']} Reglas del Concurso Anual de Juegos",
            description="Lee atentamente las reglas antes de participar.",
            color=config.COLORES['info']
        )
        
        # Periodo
        embed.add_field(
            name=f"{config.EMOJIS['fecha']} Periodo del Concurso",
            value=f"**{config.CONTEST_START_DATE.strftime('%d/%m/%Y')}** - **{config.CONTEST_END_DATE.strftime('%d/%m/%Y')}**",
            inline=False
        )
        
        # Plataformas válidas
        embed.add_field(
            name="🎮 Plataformas Válidas",
            value="• PlayStation 5\n• Steam\n\n⚠️ Solo juegos comprados o de biblioteca compartida.",
            inline=False
        )
        
        # Sistema de puntos
        puntos_text = (
            f"{config.EMOJIS['retro']} **Retro** (hasta 6ta gen): {config.PUNTOS_CATEGORIA['retro']} punto\n"
            f"{config.EMOJIS['indie']} **Indie**: {config.PUNTOS_CATEGORIA['indie']} punto\n"
            f"{config.EMOJIS['aa']} **AA**: {config.PUNTOS_CATEGORIA['aa']} puntos\n"
            f"{config.EMOJIS['aaa']} **AAA**: {config.PUNTOS_CATEGORIA['aaa']} puntos\n"
            f"{config.EMOJIS['platino']} **Platino/100%**: +{config.PUNTOS_CATEGORIA['platino']} punto adicional"
        )
        embed.add_field(
            name=f"{config.EMOJIS['puntos']} Sistema de Puntuación",
            value=puntos_text,
            inline=False
        )
        
        # Restricciones
        embed.add_field(
            name="❌ NO Permitido",
            value=(
                "• Juegos emulados\n"
                "• Mierdijuegos para platinos fáciles\n"
                "• Juegos completados antes del periodo válido"
            ),
            inline=False
        )
        
        # Re-completados
        embed.add_field(
            name="🔄 Re-completados",
            value="Está permitido volver a completar juegos que ya pasaste antes.\nObtienen puntos completos.",
            inline=False
        )
        
        # Premios
        embed.add_field(
            name="🏆 Premios",
            value=(
                "**🥇 Primer lugar:** Juego de $30 USD o menos\n\n"
                "**⚠️ Regla Especial:**\n"
                "Si Elkie gana el primer lugar, el segundo lugar recibirá un juego de $20 USD o menos."
            ),
            inline=False
        )
        
        # Proceso
        embed.add_field(
            name="📝 Cómo Participar",
            value=(
                "1. Completa un juego\n"
                "2. Usa `/registrar` para registrarlo\n"
                "3. Un admin revisará y aprobará\n"
                "4. ¡Tus puntos se suman automáticamente!"
            ),
            inline=False
        )
        
        embed.set_footer(text="Los premios están sujetos a cambios (solo en aumento)")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="ayuda", description="Muestra el centro de ayuda interactivo")
    async def ayuda(self, interaction: discord.Interaction):
        """Panel de ayuda interactivo con menú desplegable"""
        
        try:
            # Verificar si es admin usando la función existente
            from cogs.admin import is_admin_user
            is_admin = is_admin_user(interaction.user)
            
            # Crear vista con select menu
            from views.help_view import HelpView
            
            view = HelpView(is_admin=is_admin)
            
            await interaction.response.send_message(
                embed=view.get_main_embed(),
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Error en /ayuda: {e}")
            import traceback
            traceback.print_exc()
            
            embed = discord.Embed(
                title="❌ Error",
                description=f"Hubo un error al cargar la ayuda.\n```{str(e)}```",
                color=config.COLORES['rechazado']
            )
            
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utils(bot))