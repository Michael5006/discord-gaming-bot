import discord
from discord import ui
import config

class HelpView(ui.View):
    """Vista de ayuda con menú desplegable"""
    
    def __init__(self, is_admin: bool = False):
        super().__init__(timeout=180)
        self.is_admin = is_admin
        
        # Agregar el select menu
        self.add_item(HelpSelectMenu(is_admin))
    
    def get_main_embed(self) -> discord.Embed:
        """Embed principal de ayuda"""
        embed = discord.Embed(
            title="🤖 CENTRO DE AYUDA",
            description="Bienvenido al sistema de ayuda del bot del concurso.\n*Selecciona una categoría del menú para ver los comandos disponibles.*",
            color=config.COLORES['info']
        )
        
        # Categorías disponibles
        categories_text = (
            "📂 **Categorías Disponibles:**\n\n"
            "👤 **Usuario** - Comandos básicos para participantes\n"
            "📊 **Ranking** - Consulta estadísticas y posiciones\n"
            "ℹ️ **Información** - Reglas y detalles del concurso\n"
        )
        
        if self.is_admin:
            categories_text += "👑 **Admin** - Gestión y administración\n"
        
        embed.add_field(
            name="",
            value=categories_text,
            inline=False
        )
        
        embed.add_field(
            name="💡 Consejo Rápido",
            value="Para empezar a participar, usa `/registrar` para agregar un juego completado.",
            inline=False
        )
        
        embed.set_footer(text="💬 ¿Necesitas ayuda adicional? Contacta a un admin")
        
        return embed


class HelpSelectMenu(ui.Select):
    """Menú desplegable para seleccionar categorías de ayuda"""
    
    def __init__(self, is_admin: bool = False):
        options = [
            discord.SelectOption(
                label="Inicio",
                description="Volver al menú principal",
                emoji="🏠",
                value="main"
            ),
            discord.SelectOption(
                label="Comandos de Usuario",
                description="Registrar juegos, ver estadísticas personales",
                emoji="👤",
                value="user"
            ),
            discord.SelectOption(
                label="Comandos de Ranking",
                description="Consultar posiciones y estadísticas generales",
                emoji="📊",
                value="ranking"
            ),
            discord.SelectOption(
                label="Información del Concurso",
                description="Reglas, premios y fechas",
                emoji="ℹ️",
                value="info"
            ),
        ]
        
        if is_admin:
            options.append(
                discord.SelectOption(
                    label="Comandos de Admin",
                    description="Gestión de juegos y usuarios",
                    emoji="👑",
                    value="admin"
                )
            )
        
        super().__init__(
            placeholder="📂 Selecciona una categoría...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="help_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Maneja la selección del menú"""
        selected = self.values[0]
        
        if selected == "main":
            embed = self.view.get_main_embed()
        elif selected == "user":
            embed = self.get_user_commands_embed()
        elif selected == "ranking":
            embed = self.get_ranking_commands_embed()
        elif selected == "info":
            embed = self.get_info_embed()
        elif selected == "admin":
            embed = self.get_admin_commands_embed()
        
        await interaction.response.edit_message(embed=embed, view=self.view)
    
    def get_user_commands_embed(self) -> discord.Embed:
        """Comandos de usuario"""
        embed = discord.Embed(
            title="👤 COMANDOS DE USUARIO",
            description="Comandos disponibles para todos los participantes",
            color=0x5865F2  # Azul Discord
        )
        
        commands = [
            ("🎮 `/registrar`", "Registra un juego completado con búsqueda inteligente"),
            ("📋 `/mis-juegos`", "Ver todos tus juegos aprobados"),
            ("⏳ `/mis-pendientes`", "Ver juegos pendientes de aprobación"),
            ("🗑️ `/eliminar-pendiente`", "Eliminar un juego pendiente"),
            ("📍 `/mi-posicion`", "Ver tu posición actual en el ranking"),
            ("📊 `/estadisticas`", "Ver tus estadísticas detalladas"),
        ]
        
        for name, desc in commands:
            embed.add_field(name=name, value=desc, inline=False)
        
        embed.set_footer(text="💡 Tip: Los juegos deben ser aprobados por un admin para sumar puntos")
        
        return embed
    
    def get_ranking_commands_embed(self) -> discord.Embed:
        """Comandos de ranking"""
        embed = discord.Embed(
            title="📊 COMANDOS DE RANKING",
            description="Consulta posiciones y estadísticas del concurso",
            color=0x57F287  # Verde Discord
        )
        
        commands = [
            ("🏆 `/ranking`", "Ver el ranking completo con biblioteca de juegos interactiva"),
            ("📈 `/tablero`", "Dashboard completo con estadísticas y análisis"),
            ("📖 `/reglas`", "Ver las reglas completas del concurso"),
        ]
        
        for name, desc in commands:
            embed.add_field(name=name, value=desc, inline=False)
        
        embed.add_field(
            name="🎯 Sistema de Puntos",
            value=(
                "🕹️ **Retro:** 1 punto\n"
                "🎨 **Indie:** 1 punto\n"
                "🎯 **AA:** 2 puntos\n"
                "👑 **AAA:** 3 puntos\n"
                "🏆 **Platino:** +1 punto adicional"
            ),
            inline=False
        )
        
        return embed
    
    def get_info_embed(self) -> discord.Embed:
        """Información del concurso"""
        embed = discord.Embed(
            title="ℹ️ INFORMACIÓN DEL CONCURSO",
            description="Todo lo que necesitas saber sobre el concurso 2025-2027",
            color=0xFEE75C  # Amarillo Discord
        )
        
        embed.add_field(
            name="📅 Duración",
            value="**Inicio:** 25 de Diciembre 2025\n**Fin:** 1 de Enero 2027",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Premios",
            value=(
                "🥇 **1er Lugar:** $30 USD\n"
                "🥈 **2do Lugar:** $20 USD (si aplica Regla Elkie)\n\n"
                "👑 **Regla Elkie:** Si el ganador tiene marca Elkie, "
                "el segundo lugar también recibe premio."
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎮 Plataformas Permitidas",
            value="• PlayStation 5\n• Steam (PC)",
            inline=True
        )
        
        embed.add_field(
            name="📋 Reglas Básicas",
            value="• Solo juegos 100% completados\n• Platinos opcionales (+1 pt)\n• Se permiten re-completados",
            inline=True
        )
        
        embed.add_field(
            name="🔗 Enlaces Útiles",
            value="• Usa `/reglas` para ver reglas completas\n• Usa `/tablero` para ver progreso",
            inline=False
        )
        
        return embed
    
    def get_admin_commands_embed(self) -> discord.Embed:
        """Comandos de admin"""
        embed = discord.Embed(
            title="👑 COMANDOS DE ADMINISTRACIÓN",
            description="Comandos exclusivos para administradores",
            color=0xED4245  # Rojo Discord
        )
        
        review_commands = [
            ("⏳ `/pendientes`", "Ver todos los juegos pendientes"),
            ("👁️ `/revisar`", "Ver detalles de un juego pendiente"),
            ("✅ `/aprobar`", "Aprobar un juego con autocompletado"),
            ("❌ `/rechazar`", "Rechazar un juego con razón"),
        ]
        
        edit_commands = [
            ("✏️ `/editar-juego`", "Editar un juego ya aprobado"),
            ("🔧 `/modificar-pendiente`", "Modificar un juego antes de aprobar"),
            ("🗑️ `/eliminar-juego`", "Eliminar cualquier juego del sistema"),
        ]
        
        other_commands = [
            ("👑 `/marcar-elkie`", "Activar/desactivar regla Elkie para un usuario"),
        ]
        
        embed.add_field(
            name="📋 Revisión de Juegos",
            value="\n".join(f"{cmd[0]} - {cmd[1]}" for cmd in review_commands),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Edición y Gestión",
            value="\n".join(f"{cmd[0]} - {cmd[1]}" for cmd in edit_commands),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Otros",
            value="\n".join(f"{cmd[0]} - {cmd[1]}" for cmd in other_commands),
            inline=False
        )
        
        embed.set_footer(text="⚠️ Usa estos comandos con responsabilidad")
        
        return embed


class CloseButton(ui.Button):
    """Botón para cerrar el panel de ayuda"""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Cerrar Ayuda",
            emoji="❌",
            custom_id="close_help"
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content="✅ Panel de ayuda cerrado.",
            embed=None,
            view=None,
            delete_after=3
        )