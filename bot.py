import discord
from discord.ext import commands
import json
import os

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TOKEN")

STOCK_CHANNEL_ID = 1504575488834670743

STOCK_MESSAGE_ID = None
PANEL_MESSAGE_ID = None

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
    try:
        with open("stock.json", "r") as f:
            return json.load(f)
    except:
        return {
            "vehicles": [],
            "tractors": [],
            "harvesters": [],
            "haulers": [],
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
            "Sled", "Euro Hauler 1280", "Cyber Semi", "Cybertruck",
            "Train", "DG Semi", "R350 SD", "Kei Pickup",
            "Marley Pickup", "Titan X", "Titan",
            "Levi Flatbed", "Foxx Metal Tech P1",
            "R500", "Solid Hauler 47"
        },
        "tractors": {
            "Sleigh", "Vertra 135", "Vintage Tractor", "KM472",
            "Claas Xerion 5000", "Fordson", "Rusty Tractor",
            "Medal Tractor", "SOPT 925", "Foxx Metal Tech X1",
            "ER80T", "Zalter 500", "ROM2400", "Foxx Chamber 105"
        },
        "harvesters": {
            "NA CR10", "Vintage Harvester", "ActiveS7",
            "Claas 790", "Mega Baler"
        },
        "haulers": {
            "SL Medium", "Automatic Flatbed",
            "Insul Animal Trailer", "Small Log Hauler",
            "Legendary Log Transport", "Large Crop Trailer",
            "Large Box Trailer", "Vintage Flatbed",
            "Vintage Log Trailer", "Titan LH", "Titan CH",
            "Marley Liquid Hauler", "Marley Crop Hauler",
            "Kei Liquid Hauler", "Kei Crop Hauler",
            "R1950 Liquid", "DG LT", "DG CT",
            "Pace IX CH", "Pace IX LT"
        },
        "plows": {"ZC3", "NSH", "Maltex P680"},
        "cultivators": {"Swifter 180", "LAT 360", "WRXL2", "Maltex C4500 Global"},
        "seeders": {"Pronto9", "EFC 8300 Drill", "ATM 700", "Zalter-S 270", "GFS10"},
        "packs": {
            "Truck N' Trailers Pack", "DG Semi Pack",
            "Vintage Semi Pack", "1950's Truck Pack",
            "Starter Pack", "Kei Truck Pack",
            "Marley Truck Pack", "Cyber Pack",
            "Christmas Vehicle Pack", "Lumber Starter Pack",
            "Zalter Pack", "Titan Truck Pack",
            "Insul Pack", "Pace IX Pack"
        }
    }

    for cat, items in mapping.items():
        if item in items:
            return cat
    return None

# =========================
# EMBED
# =========================

def build_embed():

    embed = discord.Embed(
        title="Current Stock",
        color=0x2ecc71
    )

    emoji = {
        "vehicles":"🚗",
        "tractors":"🚜",
        "harvesters":"🌾",
        "haulers":"🚛",
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

        lines = []

        for item in items:
            name = item.get("name")
            qty = item.get("qty", 1)
            value = item.get("value", "N/A")

            lines.append(f"{qty}x {name} - {value}")

        embed.add_field(
            name=f"{emoji.get(cat,'📁')} {cat.capitalize()}",
            value="\n".join(lines),
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

    embed = build_embed()

    if STOCK_MESSAGE_ID:
        try:
            msg = await channel.fetch_message(STOCK_MESSAGE_ID)
            await msg.edit(embed=embed)
            return
        except:
            pass

    msg = await channel.send(embed=embed)
    STOCK_MESSAGE_ID = msg.id

# =========================
# PANEL SYSTEM FIX
# =========================

async def send_panel():

    global PANEL_MESSAGE_ID

    channel = bot.get_channel(STOCK_CHANNEL_ID)
    if not channel:
        return

    if PANEL_MESSAGE_ID:
        try:
            await channel.fetch_message(PANEL_MESSAGE_ID)
            return
        except:
            pass

    msg = await channel.send(
        "Stock Panel",
        view=StockPanel()
    )

    PANEL_MESSAGE_ID = msg.id

# =========================
# PANEL
# =========================

class StockPanel(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Add Stock", style=discord.ButtonStyle.success)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "Select category:",
            view=CategorySelect("add"),
            ephemeral=True
        )

    @discord.ui.button(label="Remove Stock", style=discord.ButtonStyle.danger)
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
            for c in stock.keys()
            if c != "master_list"
        ]

        self.add_item(CategoryDropdown(options, action))

class CategoryDropdown(discord.ui.Select):

    def __init__(self, options, action):
        super().__init__(placeholder="Select category", options=options)
        self.action = action

    async def callback(self, interaction: discord.Interaction):

        category = self.values[0]
        items = stock.get("master_list", [])

        filtered = [
            i for i in items
            if get_category(i) == category
        ]

        filtered = filtered[:25]

        if not filtered:
            return await interaction.response.send_message(
                "No items in this category",
                ephemeral=True
            )

        options = [
            discord.SelectOption(label=i[:100], value=i[:100])
            for i in filtered
        ]

        await interaction.response.send_message(
            "Select item:",
            view=ItemSelect(options, category, self.action),
            ephemeral=True
        )

# =========================
# ITEM SELECT
# =========================

class ItemSelect(discord.ui.View):

    def __init__(self, options, category, action):
        super().__init__(timeout=60)
        self.add_item(ItemDropdown(options, category, action))

class ItemDropdown(discord.ui.Select):

    def __init__(self, options, category, action):

        if len(options) > 25:
            options = options[:25]

        super().__init__(placeholder="Select item", options=options)

        self.category = category
        self.action = action

    async def callback(self, interaction: discord.Interaction):

        item = self.values[0]
        cat = self.category

        category_list = stock[cat]

        if self.action == "add":

            for obj in category_list:
                if obj["name"] == item:
                    obj["qty"] += 1
                    break
            else:
                category_list.append({
                    "name": item,
                    "qty": 1,
                    "value": "N/A"
                })

        else:

            for obj in category_list:
                if obj["name"] == item:
                    obj["qty"] -= 1
                    if obj["qty"] <= 0:
                        category_list.remove(obj)
                    break

        save_stock(stock)
        await update_stock()

        await interaction.response.send_message("Updated stock", ephemeral=True)

# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    await update_stock()
    await send_panel()

    bot.add_view(StockPanel())

# =========================
# RUN
# =========================

bot.run(TOKEN)