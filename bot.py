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
# LOAD STOCK SAFE
# =========================

def load_stock():
    try:
        with open("stock.json", "r") as f:
            data = json.load(f)

        # ensure master_list always exists
        if "master_list" not in data:
            data["master_list"] = []

        return data

    except Exception as e:
        print("❌ STOCK LOAD ERROR:", e)

        # fallback safe structure
        return {
            "vehicles": [],
            "tractors": [],
            "harvesters": [],
            "trailers": [],
            "plows": [],
            "cultivators": [],
            "seeders": [],
            "packs": [],
            "master_list": []
        }

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
# CATEGORY MAP
# =========================

def get_category(item):

    vehicles = {
        "Sled","Sleigh","SL Medium","Euro Hauler 1280","Cyber Semi","Cybertruck",
        "Train","DG Semi","R350 SD","Kei Pickup","Marley Pickup","Titan X",
        "Pace IX CH","Pace IX LT","Titan","Foxx Metal Tech P1","R500"
    }

    tractors = {
        "Vertra 135","Vintage Tractor","KM472","Claas Xerion 5000","Fordson",
        "Rusty Tractor","Medal Tractor","SOPT 925","Foxx Metal Tech X1",
        "ER80T","Zalter 500"
    }

    harvesters = {"NA CR10","Vintage Harvester","ActiveS7","Claas 790","Mega Baler"}

    trailers = {
        "Insul Animal Trailer","Small Log Hauler","Legendary Log Transport",
        "Levi Flatbed","Large Crop Trailer","Large Box Trailer","Vintage Flatbed",
        "Vintage Log Trailer","Titan LH","Titan CH","Solid Hauler 47",
        "Marley Liquid Hauler","Marley Crop Hauler","Kei Liquid Hauler",
        "Kei Crop Hauler","R1950 Liquid","DG LT","DG CT"
    }

    plows = {"ROM2400","ZC3","WRXL2","GFS10","NSH","Maltex P680"}
    cultivators = {"Swifter 180","LAT 360","Foxx Chamber 105","Maltex C4500 Global"}
    seeders = {"Pronto9","EFC 8300 Drill","ATM 700","Zalter-S 270"}

    packs = {
        "Truck N' Trailers Pack","DG Semi Pack","Vintage Semi Pack",
        "1950's Truck Pack","Starter Pack","Kei Truck Pack","Marley Truck Pack",
        "Cyber Pack","Christmas Vehicle Pack","Lumber Starter Pack",
        "Zalter Pack","Titan Truck Pack","Insul Pack","Pace IX Pack"
    }

    if item in vehicles: return "vehicles"
    if item in tractors: return "tractors"
    if item in harvesters: return "harvesters"
    if item in trailers: return "trailers"
    if item in plows: return "plows"
    if item in cultivators: return "cultivators"
    if item in seeders: return "seeders"
    if item in packs: return "packs"

    return None

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
        if category == "master_list":
            continue
        if not items:
            continue

        embed.add_field(
            name=f"{emoji_map.get(category,'📁')} {category.capitalize()}",
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
# ADMIN PANEL
# =========================

async def send_or_update_admin_panel():
    global ADMIN_MESSAGE_ID

    channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(
        title="🛠️ Stock Panel",
        description="Use buttons to manage stock",
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

    print("MASTER LIST:", stock.get("master_list"))

    await send_or_update_stock_panel()
    await send_or_update_admin_panel()

    bot.add_view(StockPanel())

# =========================
# BUTTON PANEL
# =========================

class StockPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="➕ Add Stock", style=discord.ButtonStyle.success, custom_id="add_stock")
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not has_permission(interaction.user):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)

        await interaction.response.send_message(
            "Select item to ADD:",
            view=MasterSelect("add"),
            ephemeral=True
        )

    @discord.ui.button(label="➖ Remove Stock", style=discord.ButtonStyle.danger, custom_id="remove_stock")
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not has_permission(interaction.user):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)

        await interaction.response.send_message(
            "Select item to REMOVE:",
            view=MasterSelect("remove"),
            ephemeral=True
        )

# =========================
# MASTER SELECT (FIXED SAFETY)
# =========================

class MasterSelect(discord.ui.View):
    def __init__(self, action):
        super().__init__(timeout=60)
        self.action = action

        items = stock.get("master_list") or []

        # HARD SAFETY
        if len(items) == 0:
            items = ["NO ITEMS LOADED"]

        options = [
            discord.SelectOption(label=str(i)[:100], value=str(i)[:100])
            for i in items
        ]

        if len(options) == 0:
            options = [discord.SelectOption(label="EMPTY LIST", value="none")]

        self.add_item(MasterDropdown(options, action))

class MasterDropdown(discord.ui.Select):
    def __init__(self, options, action):
        super().__init__(placeholder="Select item...", options=options)
        self.action = action

    async def callback(self, interaction: discord.Interaction):

        item = self.values[0]

        if item in ["none", "NO ITEMS LOADED"]:
            return await interaction.response.send_message("❌ Master list not loaded.", ephemeral=True)

        category = get_category(item)

        if not category:
            return await interaction.response.send_message("❌ Unknown category.", ephemeral=True)

        if self.action == "add":
            if item not in stock[category]:
                stock[category].append(item)

        elif self.action == "remove":
            if item in stock[category]:
                stock[category].remove(item)

        save_stock(stock)

        await send_or_update_stock_panel()

        await interaction.response.send_message(f"✅ Updated: {item}", ephemeral=True)

# =========================
# RUN
# =========================

bot.run(TOKEN)