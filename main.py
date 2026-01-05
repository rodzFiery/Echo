import discord
import os
import asyncio
import json
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web

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
            try: return json.load(f) # Now returns a dictionary for modularity
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
        amount = data.get('mc_gross', "0.00") # Grab the payment amount from PayPal

        if payment_status == 'Completed' and "|" in custom_data:
            guild_id_str, module_name = custom_data.split("|")
            
            global PREMIUM_GUILDS
            if guild_id_str not in PREMIUM_GUILDS:
                PREMIUM_GUILDS[guild_id_str] = []
            
            if module_name not in PREMIUM_GUILDS[guild_id_str]:
                PREMIUM_GUILDS[guild_id_str].append(module_name)
                with open(PREMIUM_FILE, "w") as f:
                    json.dump(PREMIUM_GUILDS, f)
                print(f"💎 MODULE ACTIVATED: {module_name} for {guild_id_str}")

                # --- NEW: SALES LOG TO YOUR DEVELOPER SERVER ---
                try:
                    dev_channel = self.get_channel(1457706030199996570)
                    if dev_channel:
                        log_emb = discord.Embed(title="💰 NEW SALE DETECTED", color=0x00ff00)
                        log_emb.add_field(name="Module", value=module_name.upper(), inline=True)
                        log_emb.add_field(name="Amount", value=f"${amount} USD", inline=True)
                        log_emb.add_field(name="Server ID", value=guild_id_str, inline=False)
                        log_emb.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M')}")
                        await dev_channel.send(embed=log_emb)
                except Exception as e:
                    print(f"Failed to log sale: {e}")

        return web.Response(text="OK")

    async def on_ready(self):
        print(f'🔥 Bot Online: {self.user}')
        await self.change_presence(activity=discord.Game(name="!askcommands"))

bot = MyBot()

@bot.command()
async def invite(ctx):
    await ctx.send(f"Add me: {discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(administrator=True))}")

# --- NEW: THE HIGH LEVEL SHOP LOBBY ---
@bot.command(name="premium")
@commands.has_permissions(administrator=True)
async def premium(ctx):
    # Add your prices here when you create new .py files!
    MODULE_PRICES = {
        "ask": "2.50",
        "casino": "3.50",
        "economy": "2.00"
    }
    
    available_modules = [f[:-3] for f in os.listdir('./cogs') if f.endswith('.py')]
    
    embed = discord.Embed(
        title="🔥 FIERY MODULE SHOP", 
        description="Select a module to unlock its premium features for this server.",
        color=0xff4500
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)

    class ShopView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)
            options = []
            for mod in available_modules:
                price = MODULE_PRICES.get(mod, "5.00") # Default $5 if price not set
                options.append(discord.SelectOption(
                    label=f"Unlock {mod.upper()}", 
                    description=f"Direct PayPal Activation - ${price}", 
                    value=f"{mod}|{price}",
                    emoji="💎"
                ))
            
            if not options:
                return # Prevent crash if no cogs exist
                
            self.select = discord.ui.Select(placeholder="Select a module to buy...", options=options)
            self.select.callback = self.select_callback
            self.add_item(self.select)

        async def select_callback(self, interaction: discord.Interaction):
            mod_name, price = self.select.values[0].split("|")
            pay_email = os.getenv('PAYPAL_EMAIL')
            custom_payload = f"{interaction.guild_id}|{mod_name}"
            
            paypal_url = (
                f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick"
                f"&business={pay_email}&amount={price}&currency_code=USD"
                f"&item_name=Fiery_{mod_name.upper()}_Module_Server_{interaction.guild_id}"
                f"&custom={custom_payload}"
            )
            
            checkout_emb = discord.Embed(title=f"🛒 Checkout: {mod_name.upper()}", color=0x00ff00)
            checkout_emb.description = (
                f"You are purchasing the **{mod_name.upper()}** module.\n"
                f"**Price:** ${price} USD\n\n"
                f"Click [**HERE TO PAY**]({paypal_url})\n\n"
                "*The module will unlock automatically after payment.*"
            )
            await interaction.response.send_message(embed=checkout_emb, ephemeral=True)

    await ctx.send(embed=embed, view=ShopView())

# --- NEW: THE ULTIMATE MODULAR DASHBOARD ---
@bot.command(name="premiumstatus")
@commands.has_permissions(administrator=True)
async def premiumstatus(ctx):
    guild_id = str(ctx.guild.id)
    # Get all .py files in cogs to see what's available
    available_modules = [f[:-3] for f in os.listdir('./cogs') if f.endswith('.py')]
    # Get what this server has bought
    owned_modules = PREMIUM_GUILDS.get(guild_id, [])

    embed = discord.Embed(title="⚔️ SERVER MODULE DASHBOARD", color=0xff4500)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    status_text = ""
    unlocked_count = 0
    
    for module in available_modules:
        if module in owned_modules:
            status_text += f"✅ **{module.upper()}**: `UNLOCKED`\n"
            unlocked_count += 1
        else:
            status_text += f"❌ **{module.upper()}**: `LOCKED` (Type `!premium` to buy)\n"
    
    # Visual Progress Bar
    total = len(available_modules)
    percent = (unlocked_count / total) * 100 if total > 0 else 0
    bar = "🟩" * unlocked_count + "⬛" * (total - unlocked_count)
    
    embed.add_field(name="Current Features", value=status_text, inline=False)
    embed.add_field(name="Unlock Progress", value=f"{bar} **{percent:.0f}%**", inline=False)
    embed.set_footer(text=f"Server ID: {guild_id} | Support your developer 🔥")
    
    await ctx.send(embed=embed)

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
