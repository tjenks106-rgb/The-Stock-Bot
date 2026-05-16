import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1504537814312685640

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
    # Server owner always allowed
    if member.guild.owner_id == member.id:
        return True

    # Role-based access
    user_roles = [role.name for role in member.roles]
    return any(role in user_roles for role in ALLOWED_ROLES)

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

    await interaction.response.send_message(
        "🗑️ All stock cleared."
    )

# =========================
# RUN BOT
# =========================

bot.run(TOKEN)