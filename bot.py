import discord
from discord.ext import commands
import json
import os

# =========================
# TOKEN
# =========================

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise Exception("❌ TOKEN missing in Railway env vars")

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
# LOAD STOCK
# =========================

def load_stock():
    try:
        with open("stock.json", "r") as f:
            data = json.load(f)
        if "master_list" not in data:
            data["master_list"] = []
        return data
    except:
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

def save_stock(data):
    with open("stock.json", "w") as f:
        json.dump(data, f, indent=4)

stock = load_stock()

# =========================
# CATEGORY MAP
# =========================

def get_category(item):

    mapping = {
        "vehicles": {
            "Sled","Sleigh","SL Medium","Euro Hauler 1280","Cyber Semi","Cybertruck",
            "Train","DG Semi","R350 SD","Kei Pickup","Marley Pickup","Titan X",
            "Pace IX CH","Pace IX LT","Titan","Foxx Metal Tech P1","R500"
        },
        "tractors": {
            "Vertra 135","Vintage Tractor","KM472","Claas Xerion 5000","Fordson",
            "Rusty Tractor","Medal Tractor","SOPT 925","Foxx Metal Tech X1",
            "ER80T","Zalter 500"
        },
        "harvesters": {"NA CR10","Vintage Harvester","ActiveS7","Claas 790","Mega Baler"},
        "trailers": {
            "Insul Animal Trailer","Small Log Hauler","Legendary Log Transport",
            "Levi Flatbed","Large Crop Trailer","Large Box Trailer","Vintage Flatbed",
            "Vintage Log Trailer","Titan LH","Titan CH","Solid Hauler 47",
            "Marley Liquid Hauler","Marley Crop Hauler","Kei Liquid Hauler",
            "Kei Crop Hauler","R1950 Liquid","DG LT","DG CT"
        },
        "plows": {"ROM2400","ZC3","WRXL2","GFS10","NSH","Maltex P680"},
        "cultivators": {"Swifter 180","LAT 360","Foxx Chamber 105","Maltex C4500 Global"},
        "seeders": {"Pronto9","EFC 8300 Drill","ATM 700","Zalter-S 270"},
        "packs": {
            "Truck N' Trailers Pack","DG Semi Pack","Vintage Semi Pack",
            "1950's Truck Pack","Starter Pack","Kei Truck Pack","Marley Truck Pack",
            "Cyber Pack","Christmas Vehicle Pack","Lumber Starter Pack",
            "Zalter Pack","Titan Truck Pack","Insul Pack","Pace IX Pack"
        }
    }

    for cat, items in mapping.items():
        if item in items:
            return cat

    return None

# =========================
# EMBED
# =========================

def build_stock_embed():
    embed = discord.Embed(title="🔥 Current Stock", color=0x39ff14)

    emoji = {
        "vehicles":"🚗",
        "tractors":"🚜",
        "harvesters":"🌾",
        "trailers":"🚛",
        "plows":"🛠️",
        "cultivators":"⚙️",
        "seeders":"🌱",
        "packs":"📦"
    }

    for cat, items in stock.items():
        if cat == "master_list":
            continue
        if not items:
            continue

        embed.add_field(
            name=f"{emoji.get(cat,'📁')} {cat.capitalize()}",
            value="\n".join(items),
            inline=False
        )

    return embed

# =========================
# UPDATE STOCK
# =========================

async def update_stock():
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

async def update_admin():
    global ADMIN_MESSAGE_ID

    channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(
        title="🛠️ Stock Panel",
        description="Manage stock below",
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
    print(f"Logged in as {bot.user}")
    await update_stock()
    await update_admin()
    bot.add_view(StockPanel())

# =========================
# MAIN PANEL
# =========================

class StockPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="➕ Add Stock", style=discord.ButtonStyle.success, custom_id="add")
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "Select category:",
            view=CategorySelect("add"),
            ephemeral=True
        )

    @discord.ui.button(label="➖ Remove Stock", style=discord.ButtonStyle.danger, custom_id="remove")
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "Select category:",
            view=CategorySelect("remove"),
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
            discord.SelectOption(label=c.capitalize(), value=c)
            for c in ["vehicles","tractors","harvesters","trailers","plows","cultivators","seeders","packs"]
        ]

        self.add_item(CategoryDropdown(options, action))

class CategoryDropdown(discord.ui.Select):
    def __init__(self, options, action):
        super().__init__(placeholder="Select category", options=options)
        self.action = action

    async def callback(self, interaction: discord.Interaction):

        category = self.values[0]

        items = stock.get("master_list", [])
        filtered = [i for i in items if get_category(i) == category]

        if not filtered:
            return await interaction.response.send_message("❌ No items", ephemeral=True)

        filtered = filtered[:25]  # DISCORD LIMIT

        options = [
            discord.SelectOption(label=i[:100], value=i[:100])
            for i in filtered
        ]

        await interaction.response.send_message(
            "Select item:",
            view(ItemSelect(options, category, self.action)),
            ephemeral=True
        )

# =========================
# ITEM SELECT
# =========================

class ItemSelect(discord.ui.View):
    def __init__(self, options, category, action):
        super().__init__(timeout=60)
        self.category = category
        self.action = action
        self.add_item(ItemDropdown(options, category, action))

class ItemDropdown(discord.ui.Select):
    def __init__(self, options, category, action):
        super().__init__(placeholder="Select item", options=options)
        self.category = category
        self.action = action

    async def callback(self, interaction: discord.Interaction):

        item = self.values[0]
        cat = self.category

        if self.action == "add":
            if item not in stock[cat]:
                stock[cat].append(item)

        else:
            if item in stock[cat]:
                stock[cat].remove(item)

        save_stock(stock)
        await update_stock()

        await interaction.response.send_message("✅ Updated", ephemeral=True)

# =========================
# RUN
# =========================

bot.run(TOKEN)