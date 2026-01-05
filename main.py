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

# Changed filename to reflect modular data structure
PREMIUM_FILE = os.path.join(DATA_DIR, "premium_modules.json")

def get_premium_data():
    if os.path.exists(PREMIUM_FILE):
        with open(PREMIUM_FILE, "r") as f:
            try: return json.load(f) # Now returns a dict: {"guild_id": ["ask", "casino"]}
            except: return {}
    return {}

# Shared global variable for the bot instance
PREMIUM_GUILDS = get_premium_data()

# 3. INITIALIZATION
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        print("--- Loading Modules ---")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Module Loaded: {filename}')
        
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
        # Expecting 'custom' to be formatted as "guild_id|module_name"
        custom_field = data.get('custom', "")
        payment_status = data.get('payment_status')

        if payment_status == 'Completed' and "|" in custom_field:
            guild_id_str, module_name = custom_field.split("|")
            
            global PREMIUM_GUILDS
            if guild_id_str not in PREMIUM_GUILDS:
                PREMIUM_GUILDS[guild_id_str] = []
            
            if module_name not in PREMIUM_GUILDS[guild_id_str]:
                PREMIUM_GUILDS[guild_id_str].append(module_name)
                with open(PREMIUM_FILE, "w") as f:
                    json.dump(PREMIUM_GUILDS, f)
                print(f"💎 MODULE ACTIVATED: {module_name} for Guild {guild_id_str}")
                
        return web.Response(text="OK")

    async def on_ready(self):
        print(f'🔥 Bot Online: {self.user}')
        await self.change_presence(activity=discord.Game(name="!askcommands"))

bot = MyBot()

@bot.command()
async def invite(ctx):
    await ctx.send(f"Add me: {discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(administrator=True))}")

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
