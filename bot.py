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

# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# FILES
# =========================

def load_stock():
    try:
        with open("stock.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_stock(data):
    with open("stock.json", "w") as f:
        json.dump(data, f, indent=4)

def load_catalog():
    try:
        with open("catalog.json", "r") as f:
            return json.load(f)
    except:
        return {}

stock = load_stock()
catalog = load_catalog()

# =========================
# PRICE LOOKUP
# =========================

def get_price(item_name: str):
    for category, items in catalog.items():
        for item in items:
            if item["name"] == item_name:
                return item.get("price", "N/A")
    return "N/A"

# =========================
# CATEGORY LOOKUP
# =========================

def get_category(item_name: str):
    for cat, items in catalog.items():
        for item in items:
            if item["name"] == item_name:
                return cat
    return None

# =========================
# EMBED (FIXED: HIDE EMPTY CATEGORIES)
# =========================

def build_embed():

    embed = discord.Embed(
        title="🔥 Current Stock",
        color=0x39ff14
    )

    if not stock:
        embed.description = "No stock available"
        return embed

    found_any = False

    for category, items in catalog.items():

        category_lines = []

        for item in items:
            name = item["name"]
            qty = stock.get(name, 0)

            if qty <= 0:
                continue

            price = item.get("price", "N/A")

            category_lines.append(
                f"**{name}**\nStock: {qty}x | 💰 {price}"
            )

        # 🚨 HIDE CATEGORY IF EMPTY
        if not category_lines:
            continue

        found_any = True

        embed.add_field(
            name=f"📦 {category.capitalize()}",
            value="\n\n".join(category_lines),
            inline=False
        )

    if not found_any:
        embed.description = "No stock available"

    return embed

# =========================
# UPDATE STOCK MESSAGE
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
# BULK SYSTEM (MODAL)
# =========================

class QuantityModal(discord.ui.Modal):
    def __init__(self, item_name, action):
        super().__init__(title=f"{action.title()} Stock")
        self.item_name = item_name
        self.action = action

        self.amount = discord.ui.TextInput(
            label="Amount",
            placeholder="Enter number (e.g. 10)",
            required=True
        )

        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):

        try:
            amount = int(self.amount.value)
        except:
            return await interaction.response.send_message(
                "❌ Please enter a valid number",
                ephemeral=True
            )

        if amount <= 0:
            return await interaction.response.send_message(
                "❌ Must be greater than 0",
                ephemeral=True
            )

        # ADD STOCK
        if self.action == "add":
            stock[self.item_name] = stock.get(self.item_name, 0) + amount

        # REMOVE STOCK
        else:
            if self.item_name in stock:
                stock[self.item_name] -= amount
                if stock[self.item_name] <= 0:
                    del stock[self.item_name]

        save_stock(stock)
        await update_stock()

        await interaction.response.send_message(
            f"✅ {self.action.title()}ed {amount}x {self.item_name}",
            ephemeral=True
        )

# =========================
# PANEL
# =========================

class StockPanel(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="➕ Add Stock",
        style=discord.ButtonStyle.success,
        custom_id="stockpanel_add"
    )
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "Select category:",
            view=CategorySelect("add"),
            ephemeral=True
        )

    @discord.ui.button(
        label="➖ Remove Stock",
        style=discord.ButtonStyle.danger,
        custom_id="stockpanel_remove"
    )
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
            for c in catalog.keys()
        ]

        self.add_item(CategoryDropdown(options, action))

class CategoryDropdown(discord.ui.Select):

    def __init__(self, options, action):
        super().__init__(placeholder="Select category", options=options)
        self.action = action

    async def callback(self, interaction: discord.Interaction):

        category = self.values[0]
        items = catalog.get(category, [])

        options = [
            discord.SelectOption(label=i["name"], value=i["name"])
            for i in items[:25]
        ]

        if not options:
            return await interaction.response.send_message(
                "❌ No items in this category",
                ephemeral=True
            )

        await interaction.response.send_message(
            "Select item:",
            view=ItemSelect(options, self.action),
            ephemeral=True
        )

# =========================
# ITEM SELECT
# =========================

class ItemSelect(discord.ui.View):

    def __init__(self, options, action):
        super().__init__(timeout=60)
        self.action = action
        self.add_item(ItemDropdown(options, action))

class ItemDropdown(discord.ui.Select):

    def __init__(self, options, action):
        super().__init__(
            placeholder="Select item",
            options=options
        )
        self.action = action

    async def callback(self, interaction: discord.Interaction):

        item = self.values[0]

        await interaction.response.send_modal(
            QuantityModal(item, self.action)
        )

# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    await update_stock()

    bot.add_view(StockPanel())

# =========================
# RUN
# =========================

bot.run(TOKEN)