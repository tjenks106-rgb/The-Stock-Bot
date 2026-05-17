import discord
from discord.ext import commands
import json
import os

# =========================
# TOKEN
# =========================

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise Exception("❌ TOKEN is missing in Railway environment variables!")

# =========================
# CONFIG
# =========================

GUILD_ID = 1504537814312685640

STOCK_CHANNEL_ID = 1504575488834670743
ADMIN_CHANNEL_ID = 1505344381509697740

STOCK_MESSAGE_ID = None
ADMIN_MESSAGE_ID = None

# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# STOCK FILE
# =========================

def load_stock():
    with open("stock.json", "r") as f:
        return json.load(f)

def save_stock(stock_data):
    with open("stock.json", "w") as f:
        json.dump(stock_data, f, indent=4)

stock = load_stock()

# =========================
# PERMISSIONS
# =========================

ALLOWED_ROLES = ["Staff", "moderator", "bot developer"]

def has_permission(member: discord.Member):
    if member.guild.owner_id == member.id:
        return True
    return any(role.name in ALLOWED_ROLES for role in member.roles)

# =========================
# EMBED
# =========================

def build_stock_embed():
    embed = discord.Embed(title="🔥 Current Stock", color=0x39ff14)

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

        embed.add_field(
            name=f"{emoji_map.get(category, '📁')} {category.capitalize()}",
            value="\n".join(items),
            inline=False
        )

    return embed

# =========================
# STOCK UPDATE
# =========================

async def send_or_update_stock_panel():
    global STOCK_MESSAGE_ID

    channel = bot.get_channel(STOCK_CHANNEL_ID)
    if not channel:
        return

    embed = build_stock_embed()

    if STOCK_MESSAGE_ID:
        try:
            msg = await channel.fetch_message(STOCK_MESSAGE_ID)
            await msg.edit(embed=embed)
            return
        except:
            STOCK_MESSAGE_ID = None

    msg = await channel.send(embed=embed)
    STOCK_MESSAGE_ID = msg.id

# =========================
# ADMIN PANEL UPDATE
# =========================

async def send_or_update_admin_panel():
    global ADMIN_MESSAGE_ID

    channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(
        title="🛠️ Stock Management Panel",
        description="Use buttons below to manage stock.",
        color=0xffa500
    )

    if ADMIN_MESSAGE_ID:
        try:
            msg = await channel.fetch_message(ADMIN_MESSAGE_ID)
            await msg.edit(embed=embed, view=StockPanel())
            return
        except:
            ADMIN_MESSAGE_ID = None

    msg = await channel.send(embed=embed, view=StockPanel())
    ADMIN_MESSAGE_ID = msg.id

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    await send_or_update_stock_panel()
    await send_or_update_admin_panel()

# =========================
# BUTTON PANEL
# =========================

class StockPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="➕ Add Stock", style=discord.ButtonStyle.success)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.channel.id != ADMIN_CHANNEL_ID:
            return await interaction.response.send_message("❌ Wrong channel.", ephemeral=True)

        if not has_permission(interaction.user):
            return await interaction.response.send_message("❌ No permission.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send(
            "📂 Select category to ADD:",
            view=CategorySelect(action="add"),
            ephemeral=True
        )

    @discord.ui.button(label="➖ Remove Stock", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.channel.id != ADMIN_CHANNEL_ID:
            return await interaction.response.send_message("❌ Wrong channel.", ephemeral=True)

        if not has_permission(interaction.user):
            return await interaction.response.send_message("❌ No permission.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send(
            "📂 Select category to REMOVE:",
            view=CategorySelect(action="remove"),
            ephemeral=True
        )

# =========================
# CATEGORY SELECT
# =========================

class CategorySelect(discord.ui.View):
    def __init__(self, action):
        super().__init__(timeout=60)
        self.action = action

        options = [
            discord.SelectOption(label=cat, value=cat)
            for cat, items in stock.items()
            if items
        ]

        self.add_item(CategoryDropdown(options, action))

class CategoryDropdown(discord.ui.Select):
    def __init__(self, options, action):
        super().__init__(placeholder="Select category...", options=options)
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]

        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send(
            "🚗 Select vehicle:",
            view=VehicleSelect(category, self.action),
            ephemeral=True
        )

# =========================
# VEHICLE SELECT
# =========================

class VehicleSelect(discord.ui.View):
    def __init__(self, category, action):
        super().__init__(timeout=60)
        self.category = category
        self.action = action

        options = [
            discord.SelectOption(label=v, value=v)
            for v in stock[category]
        ]

        self.add_item(VehicleDropdown(options, category, action))

class VehicleDropdown(discord.ui.Select):
    def __init__(self, options, category, action):
        super().__init__(placeholder="Select vehicle...", options=options)
        self.category = category
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        vehicle = self.values[0]
        cat = self.category

        if self.action == "add":
            if vehicle not in stock[cat]:
                stock[cat].append(vehicle)

        elif self.action == "remove":
            if vehicle in stock[cat]:
                stock[cat].remove(vehicle)

        save_stock(stock)

        await send_or_update_stock_panel()

        await interaction.response.send_message(
            f"✅ Updated stock: **{vehicle}**",
            ephemeral=True
        )

# =========================
# RUN
# =========================

bot.run(TOKEN)