import os
import discord
from discord.ext import commands
from datetime import timedelta
import logging
import re

from myserver import server_on

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Define constants for messages
ERROR_MESSAGES = {
    'clear_no_positive': "กรุณาใส่จำนวนที่มากกว่าศูนย์",
    'clear_missing_arg': "กรุณาระบุจำนวนข้อความที่ต้องการลบด้วย",
    'clear_bad_arg': "กรุณาระบุจำนวนข้อความเป็นตัวเลข",
    'ban_missing_arg': "กรุณาเลือกผู้ใช้ที่ต้องการแบนและระบุเหตุผลด้วย",
    'ban_bad_arg': "ไม่สามารถแบนผู้ใช้ได้ กรุณาตรวจสอบว่าคุณได้เลือกผู้ใช้ที่ถูกต้อง",
    'kick_missing_arg': "กรุณาเลือกผู้ใช้ที่ต้องการเตะและระบุเหตุผลด้วย",
    'timeout_missing_arg': "กรุณาเลือกผู้ใช้ที่ต้องการตั้งเวลาและระบุเวลาที่จะมอบหมายด้วย",
    'timeout_bad_arg': "กรุณาระบุเวลาที่ถูกต้อง เช่น 10s, 1m, 2h",
    'role_missing_arg': "กรุณาระบุการเพิ่มหรือลดบทบาท, ผู้ใช้, และบทบาท",
    'role_bad_arg': "ไม่สามารถจัดการบทบาทได้ กรุณาตรวจสอบข้อมูลที่คุณให้",
    'serverinfo_no_permission': "คุณไม่มีสิทธิ์ในการดูข้อมูลเซิร์ฟเวอร์",
    'missing_permissions': "คุณไม่มีสิทธิ์ในการใช้งานคำสั่งนี้"
}

# Command info for error messages
command_info = {
    'cl': "!cl <amount>: ลบข้อความในช่อง (Clear messages in channel)",
    'ban': "!ban <@user> [reason]: แบนผู้ใช้จากเซิร์ฟเวอร์ (Ban a user from the server)",
    'kick': "!kick <@user> [reason]: เตะผู้ใช้จากเซิร์ฟเวอร์ (Kick a user from the server)",
    'timeout': "!timeout <@user> <duration>: ตั้งเวลาให้ผู้ใช้ (Timeout a user for a duration)",
    'role': "!role <add/remove> <@user> <role>: จัดการบทบาทของผู้ใช้ (Manage user roles)",
    'serverinfo': "!serverinfo แสดงข้อมูลเซิร์ฟเวอร์ (Show server info)",
    'help': "!help แสดงคำสั่งทั้งหมด (Show all commands)"
}

# Create the bot instance with all intents
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=None)

# Securely load your token from an environment variable
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL"))  # Ensure this is an integer
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Event: When the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

# Function to send logs to the log channel
async def send_log(message):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(message)


# Unified error handler
@bot.event
async def on_command_error(ctx, error):
    # หากเกิดข้อผิดพลาด 'CommandNotFound' ให้ไม่แสดงข้อความใด ๆ
    if isinstance(error, commands.CommandNotFound):
        return  # ไม่ต้องแสดงข้อความใด ๆ หากคำสั่งไม่ถูกต้องหรือไม่มีอยู่

    # ส่วนของการจัดการข้อผิดพลาดอื่น ๆ ที่มีอยู่
    command_name = ctx.command.name if ctx.command else None

    if isinstance(error, commands.MissingRequiredArgument):
        if command_name == "cl":
            await ctx.send(ERROR_MESSAGES['clear_missing_arg'])
        elif command_name == "ban":
            await ctx.send(ERROR_MESSAGES['ban_missing_arg'])
        elif command_name == "kick":
            await ctx.send(ERROR_MESSAGES['kick_missing_arg'])
        elif command_name == "timeout":
            await ctx.send(ERROR_MESSAGES['timeout_missing_arg'])
        elif command_name == "role":
            await ctx.send(ERROR_MESSAGES['role_missing_arg'])

    elif isinstance(error, commands.BadArgument):
        if command_name == "cl":
            await ctx.send(ERROR_MESSAGES['clear_bad_arg'])
        elif command_name == "role":
            await ctx.send(ERROR_MESSAGES['role_bad_arg'])
        elif command_name == "timeout":
            await ctx.send(ERROR_MESSAGES['timeout_bad_arg'])

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(ERROR_MESSAGES['missing_permissions'])
        await send_log(f"{ctx.author} attempted to use a command without the required permissions.")

    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"เกิดข้อผิดพลาด: {str(error.original)}")

    else:
        await ctx.send(f"เกิดข้อผิดพลาด: {str(error)}")


# Function to log and respond to commands
async def log_and_respond(ctx, action, member, reason=None):
    reason = reason or "No reason provided."
    log_message = f'{action} {member.mention} for: {reason}'
    await send_log(log_message)
    await ctx.send(log_message)

# Command to clear messages in the channel
@bot.command()
@commands.has_permissions(administrator=True)
async def cl(ctx, amount: int):
    if amount < 1:
        await ctx.send(ERROR_MESSAGES['clear_no_positive'])
        return
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f'ลบข้อความ {len(deleted)} ข้อความ')

# Command to ban a member
@bot.command()
@commands.has_permissions(administrator=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await log_and_respond(ctx, "Banned", member, reason)

# Command to kick a member
@bot.command()
@commands.has_permissions(administrator=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await log_and_respond(ctx, "Kicked", member, reason)

# Command to timeout a member
@bot.command()
@commands.has_permissions(administrator=True)
async def timeout(ctx, member: discord.Member, duration: str):
    match = re.match(r'(\d+)([smh])', duration)
    if match:
        amount, unit = match.groups()
        try:
            timeout_duration = int(amount) * {'s': 1, 'm': 60, 'h': 3600}[unit]
            await member.timeout(discord.utils.utcnow() + timedelta(seconds=timeout_duration))
            await send_log(f'Timed out {member.mention} for {duration}.')
            await ctx.send(f'Timed out {member.mention} for {duration}.')
        except ValueError:
            await ctx.send(ERROR_MESSAGES['timeout_bad_arg'])
            await ctx.send(command_info['timeout'])  # Add usage info for timeout
    else:
        await ctx.send(ERROR_MESSAGES['timeout_bad_arg'])
        await ctx.send(command_info['timeout'])  # Add usage info for timeout

# Command to manage roles
@bot.command()
@commands.has_permissions(administrator=True)
async def role(ctx, action: str, member: discord.Member, *, role: discord.Role):
    if action not in ['add', 'remove']:
        await ctx.send(ERROR_MESSAGES['role_bad_arg'])
        await ctx.send(command_info['role'])  # Add usage info for role
        return

    if action == 'add':
        await member.add_roles(role)
        await log_and_respond(ctx, "Added role", member, role.name)
    else:
        await member.remove_roles(role)
        await log_and_respond(ctx, "Removed role", member, role.name)

# Command to show server info
@bot.command()
@commands.has_permissions(administrator=True)
async def serverinfo(ctx):
    embed = discord.Embed(
        title="Server Information",
        description=f"Server Name: {ctx.guild.name}\nMember Count: {ctx.guild.member_count}",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

# Command to show help information
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Help Commands", color=0x00ff00)
    for cmd, description in command_info.items():
        embed.add_field(name=cmd, value=description, inline=False)
    await ctx.send(embed=embed)

gif_url = "https://cdn.discordapp.com/attachments/1147962239618383873/1302024437813477446/9cec0437907931599f4c953f19232066.gif?ex=6729e800&is=67289680&hm=92c6d605bb7ebfcc7a8465a317ebf03910c069ccdfd882fb7ac229c035590611&"
text_embed = "BOT // POWERED BY .wavechayakon // VERSION 1.1"

@bot.command()
@commands.has_permissions(administrator=True)
async def arceusx(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Arceus X", style=discord.ButtonStyle.url, url='https://spdmteam.com/index?os=android'))

    embed = discord.Embed(
        title="🌟 Download Arceus X 🌟",
        description="คลิกปุ่มด้านล่างเพื่อดาวน์โหลด Arceus X",
        color=0xFF0000
    )
    embed.set_image(url=gif_url)  # ใส่ URL ของ GIF ที่ต้องการ
    embed.set_footer(text=text_embed)

    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def deltaandroid(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Delta-Android", style=discord.ButtonStyle.url, url='https://deltaexploits.gg/delta-executor-mobile'))

    embed = discord.Embed(
        title="🌟 Download Delta-Android 🌟",
        description="คลิกปุ่มด้านล่างเพื่อดาวน์โหลด Delta-Android",
        color=0xFF0000
    )
    embed.set_image(url=gif_url)  # ใส่ URL ของ GIF ที่ต้องการ
    embed.set_footer(text=text_embed)

    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def deltaios(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Delta-iOS", style=discord.ButtonStyle.url, url='https://deltaexploits.gg/delta-executor-ios'))

    embed = discord.Embed(
        title="🌟 Download Delta-iOS 🌟",
        description="คลิกปุ่มด้านล่างเพื่อดาวน์โหลด Delta-iOS",
        color=0xFF0000
    )
    embed.set_image(url=gif_url)  # ใส่ URL ของ GIF ที่ต้องการ
    embed.set_footer(text=text_embed)

    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def codex(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="CodeX", style=discord.ButtonStyle.url, url='https://codex.lol/android'))

    embed = discord.Embed(
        title="🌟 Download CodeX 🌟",
        description="คลิกปุ่มด้านล่างเพื่อดาวน์โหลด CodeX",
        color=0xFF0000
    )
    embed.set_image(url=gif_url)  # ใส่ URL ของ GIF ที่ต้องการ
    embed.set_footer(text=text_embed)

    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def fluxus(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Fluxus", style=discord.ButtonStyle.url, url='https://fluxteam.cc/android'))

    embed = discord.Embed(
        title="🌟 Download Fluxus 🌟",
        description="คลิกปุ่มด้านล่างเพื่อดาวน์โหลด Fluxus",
        color=0xFF0000
    )
    embed.set_image(url=gif_url)  # ใส่ URL ของ GIF ที่ต้องการ
    embed.set_footer(text=text_embed)

    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def appleware(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Apple-Ware", style=discord.ButtonStyle.url, url='https://appleware.dev/download'))

    embed = discord.Embed(
        title="🌟 Download Apple-Ware 🌟",
        description="คลิกปุ่มด้านล่างเพื่อดาวน์โหลด Apple-Ware",
        color=0xFF0000
    )
    embed.set_image(url=gif_url)  # ใส่ URL ของ GIF ที่ต้องการ
    embed.set_footer(text=text_embed)

    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def cryptic(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Cryptic", style=discord.ButtonStyle.url, url='https://getcryptic.net/'))

    embed = discord.Embed(
        title="🌟 Download Cryptic 🌟",
        description="คลิกปุ่มด้านล่างเพื่อดาวน์โหลด Cryptic",
        color=0xFF0000
    )
    embed.set_image(url=gif_url)  # ใส่ URL ของ GIF ที่ต้องการ
    embed.set_footer(text=text_embed)

    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def solara(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Solara", style=discord.ButtonStyle.url, url='https://getsolara.dev/download'))

    embed = discord.Embed(
        title="🌟 Download Solara 🌟",
        description="คลิกปุ่มด้านล่างเพื่อดาวน์โหลด Solara",
        color=0xFF0000
    )
    embed.set_image(url=gif_url)  # ใส่ URL ของ GIF ที่ต้องการ
    embed.set_footer(text=text_embed)

    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def wave(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Wave", style=discord.ButtonStyle.url, url='https://getwave.gg/'))

    embed = discord.Embed(
        title="🌟 Download Wave 🌟",
        description="คลิกปุ่มด้านล่างเพื่อดาวน์โหลด Wave",
        color=0xFF0000
    )
    embed.set_image(url=gif_url)  # ใส่ URL ของ GIF ที่ต้องการ
    embed.set_footer(text=text_embed)

    await ctx.send(embed=embed, view=view)

server_on()

# Run the bot
bot.run(TOKEN)
