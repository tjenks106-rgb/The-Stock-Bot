import discord
from discord.ext import commands
import json
import os

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1504537814312685640
STOCK_CHANNEL_ID = 1504575488834670743
ADMIN_CHANNEL_ID = 1505344381509697740

STOCK_MESSAGE_ID = None

# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

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
            "trailers_haulers": [],
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
            "Sled",
            "Train",
            "Cybertruck",
            "Cyber Semi",
            "Vintage Semi",
            "Titan",
            "Titan X",
            "R500",
            "Levi Flatbed",
            "Solid Hauler 47",
            "DG Semi",
            "R350 SD",
            "Kei Pickup",
            "Marley Pickup",
            "Foxx Metal Tech P1"
        },

        "tractors": {
            "Sleigh",
            "Vertra 135",
            "Vintage Tractor",
            "KM472",
            "Claas Xerion 5000",
            "Fordson",
            "Rusty Tractor",
            "Medal Tractor",
            "SOPT 925",
            "Foxx Metal Tech X1",
            "ER80T",
            "Zalter 500",
            "ROM2400",
            "Foxx Chamber 105"
        },

        "harvesters": {
            "NA CR10",
            "Vintage Harvester",
            "ActiveS7",
            "Claas 790",
            "Mega Baler"
        },

        "trailers_haulers": {
            "SL Medium",
            "Automatic Flatbed",
            "Euro Hauler 1280",
            "Insul Animal",
            "Small Log Hauler",
            "Legendary Log Transport",
            "Large Crop Trailer",
            "Large Box Trailer",
            "Vintage Flatbed",
            "Vintage Log",
            "Titan LH",
            "Titan CH",
            "Marley Liquid",
            "Marley Crop",
            "Kei Liquid",
            "Kei Crop",
            "R1950 Liquid",
            "DG LT",
            "DG CT",
            "Pace IX CH",
            "Pace IX LT",
            "Solid Hauler 4700"
        },

        "plows": {
            "ZC3",
            "NSH",
            "Maltex P680"
        },

        "cultivators": {
            "Swifter 180",
            "LAT 360",
            "WRXL2",
            "Maltex C4500 Global"
        },

        "seeders": {
            "Pronto9",
            "EFC 8300 Drill",
            "ATM 700",
            "Zalter-S 270",
            "GFS10"
        },

        "packs": {
            "Truck N' Trailers Pack",
            "DG Semi Pack",
            "Vintage Semi Pack",
            "1950's Truck Pack",
            "Starter Pack",
            "Kei Truck Pack",
            "Marley Truck Pack",
            "Cyber Pack",
            "Christmas Vehicle Pack",
            "Lumber Starter Pack",
            "Zalter Pack",
            "Titan Truck Pack",
            "Insul Pack",
            "Pace IX Pack"
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
        title="🔥 Current Stock",
        color=0x39ff14
    )

    emoji = {
        "vehicles": "🚗",
        "tractors": "🚜",
        "harvesters": "🌾",
        "trailers_haulers": "🚛",
        "plows": "🛠️",
        "cultivators": "⚙️",
        "seeders": "🌱",
        "packs": "📦"
    }

    for cat, items in stock.items():

        if cat == "master_list":
            continue

        if not items:
            continue

        formatted_items = []

        for item in items:

            # NEW FORMAT
            if isinstance(item, dict):

                name = item.get("name", "Unknown")
                price = item.get("price", "No Value")

                formatted_items.append(
                    f"• {name} — `{price}`"
                )

            # OLD FORMAT
            else:

                formatted_items.append(
                    f"• {item}"
                )

        value_text = "\n".join(formatted_items)

        if len(value_text) > 1024:
            value_text = value_text[:1000] + "\n..."

        embed.add_field(
            name=f"{emoji.get(cat,'📁')} {cat.replace('_', ' ').title()}",
            value=value_text,
            inline=False
        )

    embed.set_footer(
        text="Limited • Premium • Event Vehicles"
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
# STOCK PANEL
# =========================

class StockPanel(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

    @discord.ui.button(
        label="➕ Add Stock",
        style=discord.ButtonStyle.success,
        custom_id="add_stock"
    )
    async def add(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            "Select category:",
            view=CategorySelect("add"),
            ephemeral=True
        )

    @discord.ui.button(
        label="➖ Remove Stock",
        style=discord.ButtonStyle.danger,
        custom_id="remove_stock"
    )
    async def remove(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

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

            discord.SelectOption(
                label=c.replace("_", " ").title(),
                value=c
            )

            for c in [
                "vehicles",
                "tractors",
                "harvesters",
                "trailers_haulers",
                "plows",
                "cultivators",
                "seeders",
                "packs"
            ]
        ]

        self.add_item(
            CategoryDropdown(options, action)
        )

class CategoryDropdown(discord.ui.Select):

    def __init__(self, options, action):

        super().__init__(
            placeholder="Select category",
            options=options
        )

        self.action = action

    async def callback(self, interaction: discord.Interaction):

        category = self.values[0]

        items = stock.get("master_list", [])

        filtered = [

            i for i in items

            if get_category(
                i["name"] if isinstance(i, dict) else i
            ) == category
        ]

        filtered = filtered[:25]

        if not filtered:

            return await interaction.response.send_message(
                "❌ No items found",
                ephemeral=True
            )

        options = []

        for i in filtered:

            if isinstance(i, dict):

                label = i.get("name", "Unknown")

            else:

                label = str(i)

            options.append(

                discord.SelectOption(
                    label=label[:100],
                    value=label[:100]
                )
            )

        await interaction.response.send_message(
            "Select item:",
            view=ItemSelect(
                options,
                category,
                self.action
            ),
            ephemeral=True
        )

# =========================
# ITEM SELECT
# =========================

class ItemSelect(discord.ui.View):

    def __init__(self, options, category, action):

        super().__init__(timeout=60)

        self.add_item(
            ItemDropdown(
                options,
                category,
                action
            )
        )

class ItemDropdown(discord.ui.Select):

    def __init__(self, options, category, action):

        super().__init__(
            placeholder="Select item",
            options=options[:25]
        )

        self.category = category
        self.action = action

    async def callback(self, interaction: discord.Interaction):

        selected = self.values[0]

        category_items = stock[self.category]

        found_item = None

        for item in stock["master_list"]:

            if isinstance(item, dict):

                if item.get("name") == selected:
                    found_item = item
                    break

            else:

                if item == selected:
                    found_item = item
                    break

        if not found_item:

            return await interaction.response.send_message(
                "❌ Item not found",
                ephemeral=True
            )

        exists = False

        for item in category_items:

            if isinstance(item, dict):

                if item.get("name") == selected:
                    exists = True

            else:

                if item == selected:
                    exists = True

        if self.action == "add":

            if not exists:
                category_items.append(found_item)

        else:

            stock[self.category] = [

                i for i in category_items

                if (
                    i.get("name") if isinstance(i, dict) else i
                ) != selected
            ]

        save_stock(stock)

        await update_stock()

        await interaction.response.send_message(
            "✅ Stock updated",
            ephemeral=True
        )

# =========================
# READY
# =========================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    bot.add_view(StockPanel())

    await update_stock()

# =========================
# RUN
# =========================

bot.run(TOKEN)