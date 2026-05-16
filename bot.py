import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1504537814312685640

# =========================
# STOCK CONFIG (NEW)
# =========================

STOCK_CHANNEL_ID = 1504575488834670743  # <-- CHANGE THIS TO YOUR STOCK CHANNEL
STOCK_MESSAGE_ID = 1505344381509697740  # will auto-create or reuse message

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# STOCK FILE HANDLING
# =========================

def load_stock():
    with open("stock.json", "r") as f:
        return json.load(f)

def save_stock(stock_data):
    with open("stock.json", "w") as f:
        json.dump(stock_data, f, indent=4)

stock = load_stock()

# =========================
# ROLE CONFIG
# =========================

ALLOWED_ROLES = ["Staff", "Moderator", "Bot Developer"]

def has_permission(member: discord.Member):
    if member.guild.owner_id == member.id:
        return True

    user_roles = [role.name for role in member.roles]
    return any(role in user_roles for role in ALLOWED_ROLES)

# =========================
# STOCK MESSAGE UPDATER (NEW)
# =========================

async def update_stock_message():
    global STOCK_MESSAGE_ID

    channel = bot.get_channel(STOCK_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(
        title="🔥 Current Stock",
        color=0x39ff14
    )

    emoji_map = {
        "vehicles": "🚗",
        "tractors": "🚜",
        "harvesters": "🌾",
        "trailers": "🚛",
        "plows": "🛠️",
        "cultivators": "⚙️",
        "seeders": "🌱",
        "packs": "📦"
    }

    for category, items in stock.items():
        emoji = emoji_map.get(category, "📁")

        if len(items) == 0:
            value = "❌ Out of Stock"
        else:
            value = "\n".join(items)

        embed.add_field(
            name=f"{emoji} {category.capitalize()}",
            value=value,
            inline=False
        )

    embed.set_footer(text="Limited • Premium • Event Vehicles")

    # edit existing message if it exists
    if STOCK_MESSAGE_ID:
        try:
            msg = await channel.fetch_message(STOCK_MESSAGE_ID)
            await msg.edit(embed=embed)
            return
        except:
            pass

    # create new message if none exists
    msg = await channel.send(embed=embed)
    STOCK_MESSAGE_ID = msg.id

# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

    print(f"✅ {bot.user} is online!")

# =========================
# STOCK VIEW COMMAND
# (unchanged - optional use)
# =========================

@bot.tree.command(
    name="stock",
    description="View dealership stock",
    guild=discord.Object(id=GUILD_ID)
)
async def stock_command(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🔥 Current Stock",
        color=0x39ff14
    )

    emoji_map = {
        "vehicles": "🚗",
        "tractors": "🚜",
        "harvesters": "🌾",
        "trailers": "🚛",
        "plows": "🛠️",
        "cultivators": "⚙️",
        "seeders": "🌱",
        "packs": "📦"
    }

    for category, items in stock.items():
        if not items:
            continue

        emoji = emoji_map.get(category, "📁")

        embed.add_field(
            name=f"{emoji} {category.capitalize()}",
            value="\n".join(items),
            inline=False
        )

    embed.set_footer(text="Limited • Premium • Event Vehicles")

    await interaction.response.send_message(embed=embed)

# =========================
# ADD STOCK
# =========================

@bot.tree.command(
    name="addstock",
    description="Add item to stock",
    guild=discord.Object(id=GUILD_ID)
)
async def addstock(interaction: discord.Interaction, category: str, item: str):

    if not interaction.guild:
        return

    member = interaction.user

    if not has_permission(member):
        await interaction.response.send_message(
            "❌ You do not have permission.",
            ephemeral=True
        )
        return

    category = category.lower()

    if category not in stock:
        await interaction.response.send_message(
            "❌ Invalid category.",
            ephemeral=True
        )
        return

    stock[category].append(item)
    save_stock(stock)

    await update_stock_message()

    await interaction.response.send_message(
        f"✅ Added **{item}** to **{category}**."
    )

# =========================
# REMOVE STOCK
# =========================

@bot.tree.command(
    name="removestock",
    description="Remove item from stock",
    guild=discord.Object(id=GUILD_ID)
)
async def removestock(interaction: discord.Interaction, category: str, item: str):

    if not interaction.guild:
        return

    member = interaction.user

    if not has_permission(member):
        await interaction.response.send_message(
            "❌ You do not have permission.",
            ephemeral=True
        )
        return

    category = category.lower()

    if category not in stock:
        await interaction.response.send_message(
            "❌ Invalid category.",
            ephemeral=True
        )
        return

    if item in stock[category]:
        stock[category].remove(item)
        save_stock(stock)

        await update_stock_message()

        await interaction.response.send_message(
            f"❌ Removed **{item}** from **{category}**."
        )
    else:
        await interaction.response.send_message(
            "❌ Item not found.",
            ephemeral=True
        )

# =========================
# CLEAR STOCK
# =========================

@bot.tree.command(
    name="clearstock",
    description="Clear all stock",
    guild=discord.Object(id=GUILD_ID)
)
async def clearstock(interaction: discord.Interaction):

    if not interaction.guild:
        return

    member = interaction.user

    if not has_permission(member):
        await interaction.response.send_message(
            "❌ You do not have permission.",
            ephemeral=True
        )
        return

    for category in stock:
        stock[category] = []

    save_stock(stock)

    await update_stock_message()

    await interaction.response.send_message(
        "🗑️ All stock cleared."
    )

# =========================
# RUN BOT
# =========================

bot.run(TOKEN)