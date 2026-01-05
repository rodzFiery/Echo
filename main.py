import discord
import os
import asyncio
import json
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
from datetime import datetime, timedelta, timezone

# 1. SETUP & SECRETS
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PAYPAL_EMAIL = os.getenv('PAYPAL_EMAIL')
PORT = int(os.getenv("PORT", 8080))

# 2. PERSISTENT STORAGE (Railway Volume)
DATA_DIR = "/app/data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

PREMIUM_FILE = os.path.join(DATA_DIR, "premium_guilds.json")

def get_premium_list():
    if os.path.exists(PREMIUM_FILE):
        with open(PREMIUM_FILE, "r") as f:
            try: 
                data = json.load(f)
                # Management Fix: Ensure we always treat this as a dictionary
                return data if isinstance(data, dict) else {}
            except: return {}
    return {}

# Shared global variable for the bot instance
PREMIUM_GUILDS = get_premium_list()

# 3. INITIALIZATION
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        print("--- Loading Modules ---")
        # Automatically load everything inside the /cogs folder
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Module Loaded: {filename}')
        
        # Start the Webhook Server
        self.loop.create_task(self.start_webhook_server())
        # Start the Expiry Checker (Runs every hour)
        self.loop.create_task(self.check_subscriptions_expiry())

    async def check_subscriptions_expiry(self):
        """Background task to remove expired monthly subscriptions"""
        while True:
            await asyncio.sleep(3600) # Wait 1 hour
            now = datetime.now(timezone.utc).timestamp()
            changed = False
            
            global PREMIUM_GUILDS
            for guild_id in list(PREMIUM_GUILDS.keys()):
                # Filter out modules where the timestamp is in the past
                if not isinstance(PREMIUM_GUILDS[guild_id], dict):
                    continue
                    
                original_count = len(PREMIUM_GUILDS[guild_id])
                PREMIUM_GUILDS[guild_id] = {
                    mod: expiry for mod, expiry in PREMIUM_GUILDS[guild_id].items() 
                    if expiry > now
                }
                if len(PREMIUM_GUILDS[guild_id]) != original_count:
                    changed = True
            
            if changed:
                with open(PREMIUM_FILE, "w") as f:
                    json.dump(PREMIUM_GUILDS, f)
                print("🧹 Cleaned up expired subscriptions.")

    async def start_webhook_server(self):
        app = web.Application()
        app.router.add_post('/paypal-webhook', self.handle_paypal_webhook)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        print(f"📡 Webhook Server active on port {PORT}")

    async def handle_paypal_webhook(self, request):
        data = await request.post()
        # Custom now sends "GUILD_ID|MODULE_NAME"
        custom_data = data.get('custom', "")
        payment_status = data.get('payment_status')
        amount_str = data.get('mc_gross', "0.00")
        amount = float(amount_str) # Grab the payment amount from PayPal

        if payment_status == 'Completed' and "|" in custom_data:
            guild_id_str, module_name = custom_data.split("|")
            
            # --- DYNAMIC DURATION LOGIC ---
            days_to_add = 30
            if amount >= 15.0: days_to_add = 180
            elif amount >= 7.5: days_to_add = 90
            elif amount >= 5.0: days_to_add = 60
            
            expiry_date = datetime.now(timezone.utc) + timedelta(days=days_to_add)
            expiry_timestamp = expiry_date.timestamp()

            global PREMIUM_GUILDS
            if guild_id_str not in PREMIUM_GUILDS:
                PREMIUM_GUILDS[guild_id_str] = {} 
            
            # Store the module with its specific expiry time
            PREMIUM_GUILDS[guild_id_str][module_name] = expiry_timestamp
            
            with open(PREMIUM_FILE, "w") as f:
                json.dump(PREMIUM_GUILDS, f)
            print(f"💎 {days_to_add} DAYS ACTIVATED: {module_name} for {guild_id_str}")

            # --- AUTOMATED SUCCESS BROADCAST TO CUSTOMER SERVER ---
            try:
                target_guild = self.get_guild(int(guild_id_str))
                if target_guild:
                    chan = next((c for c in target_guild.text_channels if c.permissions_for(target_guild.me).send_messages), None)
                    if chan:
                        success_emb = discord.Embed(title=f"💎 {days_to_add}-DAY PREMIUM UNLOCKED", color=0x00ff00)
                        success_emb.description = f"The **{module_name.upper()}** module has been activated! Enjoy your new high-level features.\n\n**Expiry:** <t:{int(expiry_timestamp)}:F>"
                        if os.path.exists("fierylogo.jpg"):
                            file = discord.File("fierylogo.jpg", filename="logo.png")
                            success_emb.set_thumbnail(url="attachment://logo.png")
                            await chan.send(file=file, embed=success_emb)
                        else:
                            await chan.send(embed=success_emb)
            except Exception as e:
                print(f"Broadcast Error: {e}")

            # --- SALES LOG TO YOUR DEVELOPER SERVER ---
            try:
                dev_channel = self.get_channel(1457706030199996570)
                if dev_channel:
                    log_emb = discord.Embed(title="💰 NEW SALE DETECTED", color=0x00ff00)
                    log_emb.add_field(name="Module", value=module_name.upper(), inline=True)
                    log_emb.add_field(name="Tier", value=f"{days_to_add} Days", inline=True)
                    log_emb.add_field(name="Amount", value=f"${amount} USD", inline=True)
                    log_emb.add_field(name="Server ID", value=guild_id_str, inline=False)
                    log_emb.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M')}")
                    if os.path.exists("fierylogo.jpg"):
                        f_log = discord.File("fierylogo.jpg", filename="logo_log.png")
                        log_emb.set_thumbnail(url="attachment://logo_log.png")
                        await dev_channel.send(file=f_log, embed=log_emb)
                    else:
                        await dev_channel.send(embed=log_emb)
            except Exception as e:
                print(f"Failed to log sale: {e}")

        return web.Response(text="OK")

    async def on_ready(self):
        print(f'🔥 Bot Online: {self.user}')
        await self.change_presence(activity=discord.Game(name="!fiery | !ask"))

bot = MyBot()

@bot.command()
async def invite(ctx):
    await ctx.send(f"Add me: {discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(administrator=True))}")

# --- MASTER COMMAND DIRECTORY ---
@bot.command(name="fiery")
async def fiery(ctx):
    embed = discord.Embed(title="⚔️ FIERY COMMAND DIRECTORY", color=0xff4500)
    embed.description = "Explore the full potential of your server with our modules."
    
    logo_file = None
    if os.path.exists("fierylogo.jpg"):
        logo_file = discord.File("fierylogo.jpg", filename="fiery_main.png")
        embed.set_thumbnail(url="attachment://fiery_main.png")

    for cog_name, cog_object in bot.cogs.items():
        commands_list = cog_object.get_commands()
        if commands_list:
            cmd_text = " ".join([f"`!{c.name}`" for c in commands_list if not c.hidden])
            embed.add_field(name=f"📦 {cog_name.replace('Dungeon', '')} Module", value=cmd_text, inline=False)

    embed.add_field(name="🛠️ Core System", value="`!premium` `!premiumstatus` `!invite` `!fiery`", inline=False)
    embed.set_footer(text="Type !premium to expand your arsenal.")
    
    if logo_file:
        await ctx.send(file=logo_file, embed=embed)
    else:
        await ctx.send(embed=embed)

# --- THE HIGH LEVEL SHOP LOBBY ---
@bot.command(name="premium")
@commands.has_permissions(administrator=True)
async def premium(ctx):
    available_modules = [f[:-3] for f in os.listdir('./cogs') if f.endswith('.py')]
    
    embed = discord.Embed(
        title="🔥 FIERY MODULE SHOP", 
        description="Select the module you wish to upgrade to view our **Payment Tiers**.",
        color=0xff4500
    )
    
    logo_file = None
    if os.path.exists("fierylogo.jpg"):
        logo_file = discord.File("fierylogo.jpg", filename="shop_logo.png")
        embed.set_thumbnail(url="attachment://shop_logo.png")

    class TierView(discord.ui.View):
        def __init__(self, module):
            super().__init__(timeout=180)
            self.module = module
            plans = [
                ("30 Days", "2.50", "🥉 Bronze Tier"),
                ("60 Days", "5.00", "🥈 Silver Tier"),
                ("90 Days", "7.50", "🥇 Gold Tier"),
                ("180 Days", "15.00", "💎 Diamond Tier")
            ]
            options = []
            for label, price, emoji_name in plans:
                options.append(discord.SelectOption(
                    label=f"{label} - ${price}", 
                    value=price, 
                    emoji=emoji_name.split()[0], 
                    description=f"Unlock {module.upper()} for {label}"
                ))
            
            self.select = discord.ui.Select(placeholder="Choose your duration tier...", options=options)
            self.select.callback = self.tier_callback
            self.add_item(self.select)

        async def tier_callback(self, interaction: discord.Interaction):
            price = self.select.values[0]
            pay_email = os.getenv('PAYPAL_EMAIL')
            custom_payload = f"{interaction.guild_id}|{self.module}"
            
            paypal_url = (
                f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick"
                f"&business={pay_email}&amount={price}&currency_code=USD"
                f"&item_name=Fiery_{self.module.upper()}_Access&custom={custom_payload}"
            )
            
            final_emb = discord.Embed(title="🛒 SECURE CHECKOUT", color=0x00ff00)
            final_emb.description = (
                f"**Module:** {self.module.upper()}\n"
                f"**Price:** ${price} USD\n\n"
                f"Click [**HERE TO PAY VIA PAYPAL**]({paypal_url})\n\n"
                "*Activation is immediate after payment completes.*"
            )
            await interaction.response.send_message(embed=final_emb, ephemeral=True)

    class ModuleSelectView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)
            options = [discord.SelectOption(label=m.upper(), value=m, emoji="📦") for m in available_modules]
            self.select = discord.ui.Select(placeholder="Select a module to view plans...", options=options)
            self.select.callback = self.module_callback
            self.add_item(self.select)

        async def module_callback(self, interaction: discord.Interaction):
            selected_mod = self.select.values[0]
            await interaction.response.send_message(f"✨ Viewing plans for **{selected_mod.upper()}**:", view=TierView(selected_mod), ephemeral=True)

    if logo_file:
        await ctx.send(file=logo_file, embed=embed, view=ModuleSelectView())
    else:
        await ctx.send(embed=embed, view=ModuleSelectView())

# --- THE ULTIMATE MODULAR DASHBOARD (FIXED LOGIC) ---
@bot.command(name="premiumstatus")
@commands.has_permissions(administrator=True)
async def premiumstatus(ctx):
    guild_id = str(ctx.guild.id)
    # Get all .py files in cogs to see what's available
    available_modules = [f[:-3] for f in os.listdir('./cogs') if f.endswith('.py')]
    # Get the dictionary for this server
    # FIX: We must ensure this is treated as a dict
    guild_data = PREMIUM_GUILDS.get(guild_id, {})

    embed = discord.Embed(title="⚔️ SERVER MODULE DASHBOARD", color=0xff4500)
    
    logo_file = None
    if os.path.exists("fierylogo.jpg"):
        logo_file = discord.File("fierylogo.jpg", filename="status_logo.png")
        embed.set_thumbnail(url="attachment://status_logo.png")
    
    status_text = ""
    unlocked_count = 0
    now = datetime.now(timezone.utc).timestamp()
    
    for module in available_modules:
        # FIX: Access the timestamp from the guild_data dictionary
        expiry = guild_data.get(module) if isinstance(guild_data, dict) else None
        
        if expiry and float(expiry) > now:
            # Show expiry date using Discord Timestamps (Relative :R)
            status_text += f"✅ **{module.upper()}**: `Expires` <t:{int(expiry)}:R>\n"
            unlocked_count += 1
        else:
            status_text += f"❌ **{module.upper()}**: `LOCKED` (Type `!premium` to buy)\n"
    
    # Visual Progress Bar
    total = len(available_modules)
    percent = (unlocked_count / total) * 100 if total > 0 else 0
    bar = "🟩" * unlocked_count + "⬛" * (total - unlocked_count)
    
    embed.add_field(name="Subscription Status", value=status_text, inline=False)
    embed.add_field(name="Unlock Progress", value=f"{bar} **{percent:.0f}%**", inline=False)
    embed.set_footer(text=f"Server ID: {guild_id} | Support your developer 🔥")
    
    if logo_file:
        await ctx.send(file=logo_file, embed=embed)
    else:
        await ctx.send(embed=embed)

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
