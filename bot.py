import discord
from discord.ext import commands
import config
import asyncio
import os

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Crear el bot
bot = commands.Bot(
    command_prefix='!',  # Prefix para comandos de texto (opcional)
    intents=intents,
    help_command=None  # Desactivamos el comando help por defecto
)

# Evento: Bot está listo
@bot.event
async def on_ready():
    print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print(f'✅ Bot conectado exitosamente!')
    print(f'👤 Usuario: {bot.user.name}')
    print(f'🆔 ID: {bot.user.id}')
    print(f'🌐 Servidores: {len(bot.guilds)}')
    print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

    # Inicializar base de datos
    from models.database import init_db
    await init_db()
    
    # Sincronizar comandos slash
    try:
        if config.GUILD_ID:
            guild = discord.Object(id=int(config.GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f'✅ Comandos sincronizados en servidor de prueba')
        else:
            await bot.tree.sync()
            print(f'✅ Comandos sincronizados globalmente')
    except Exception as e:
        print(f'❌ Error al sincronizar comandos: {e}')
    
    print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

# Evento: Cuando alguien se une al servidor
@bot.event
async def on_member_join(member):
    print(f'👋 {member.name} se unió al servidor')

# Comando de prueba simple
@bot.tree.command(name="ping", description="Verifica si el bot está funcionando")
async def ping(interaction: discord.Interaction):
    """Comando simple para probar que el bot responde"""
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"El bot está funcionando correctamente.",
        color=config.COLORES['info']
    )
    embed.add_field(name="Latencia", value=f"{latency}ms")
    
    await interaction.response.send_message(embed=embed)

# Comando de prueba con información del bot
@bot.tree.command(name="info", description="Información sobre el bot")
async def info(interaction: discord.Interaction):
    """Muestra información básica del bot"""
    embed = discord.Embed(
        title=f"{config.EMOJIS['info']} Información del Bot",
        description="Bot para el concurso anual de juegos completados",
        color=config.COLORES['info']
    )
    
    embed.add_field(
        name=f"{config.EMOJIS['fecha']} Periodo del Concurso",
        value=f"{config.CONTEST_START_DATE.strftime('%d/%m/%Y')} - {config.CONTEST_END_DATE.strftime('%d/%m/%Y')}",
        inline=False
    )
    
    embed.add_field(
        name=f"{config.EMOJIS['puntos']} Sistema de Puntos",
        value=(
            f"{config.EMOJIS['retro']} Retro: {config.PUNTOS_CATEGORIA['retro']} punto\n"
            f"{config.EMOJIS['indie']} Indie: {config.PUNTOS_CATEGORIA['indie']} punto\n"
            f"{config.EMOJIS['aa']} AA: {config.PUNTOS_CATEGORIA['aa']} puntos\n"
            f"{config.EMOJIS['aaa']} AAA: {config.PUNTOS_CATEGORIA['aaa']} puntos\n"
            f"{config.EMOJIS['platino']} Platino: +{config.PUNTOS_CATEGORIA['platino']} punto"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Plataformas Válidas",
        value=", ".join(config.PLATAFORMAS),
        inline=False
    )
    
    embed.set_footer(text=f"Bot creado para el concurso de {interaction.guild.name}")
    
    await interaction.response.send_message(embed=embed)

# Función para cargar cogs (módulos)
async def load_cogs():
    """Carga todos los módulos (cogs) del bot"""
    print("Cargando módulos...")
    
    # Lista de cogs a cargar
    cogs_to_load = ['games', 'admin', 'ranking', 'utils']
    
    for cog in cogs_to_load:
        try:
            await bot.load_extension(f'cogs.{cog}')
            print(f'✅ Módulo cargado: {cog}')
        except Exception as e:
            print(f'❌ Error al cargar {cog}: {e}')
    
    print(f"✅ Módulos cargados: {len(cogs_to_load)}")

# Función principal
async def main():
    async with bot:
        await load_cogs()
        await bot.start(config.DISCORD_TOKEN)

# Ejecutar el bot
if __name__ == '__main__':
    asyncio.run(main())