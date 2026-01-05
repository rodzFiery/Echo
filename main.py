import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# 1. Load environment variables for security
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TOPGG_TOKEN = os.getenv('TOPGG_TOKEN') # Prepared for Top.gg API

# --- Railway Variable Verification ---
if TOKEN is None:
    print("ERROR: DISCORD_TOKEN not found in the environment.")
    print("If you are on Railway, check the 'Variables' tab.")
    exit(1)

# 2. Define Bot Intents
intents = discord.Intents.default()
intents.message_content = True  
intents.members = True          

# 3. Initialize the Bot
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )

    # Internal Bridge for built-in functionality
    async def setup_hook(self):
        print("--- Initializing Internal Systems ---")
        # This still checks for cogs if you decide to add them later, 
        # but the main logic is now contained here.
        if not os.path.exists('./cogs'):
            os.makedirs('./cogs')
        
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Bridge established for extension: {filename}')
                except Exception as e:
                    print(f'Extension error {filename}: {e}')
        print("--- Systems Ready ---")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        # Setting the status for Top.gg visibility
        await self.change_presence(activity=discord.Game(name="!invite | top.gg"))
        print('Bot is online and masked for Railway.')

    async def on_connect(self):
        print(f"Bridge successfully pulled the token from the environment.")

    # --- Integrated Events for Top.gg tracking ---
    async def on_guild_join(self, guild):
        print(f"New 'download' detected. Joined: {guild.name}")

# 4. Instantiate Bot
bot = MyBot()

# --- Integrated Commands ---
@bot.command()
async def invite(ctx):
    """Generates the invite link for users to 'download' the bot."""
    perms = discord.Permissions(administrator=True)
    link = discord.utils.oauth_url(bot.user.id, permissions=perms)
    await ctx.send(f"Add me to your server: {link}")

@bot.command()
async def stats(ctx):
    """Displays bot reach for Top.gg requirements."""
    server_count = len(bot.guilds)
    embed = discord.Embed(title="Bot Metrics", color=discord.Color.green())
    embed.add_field(name="Active Servers", value=str(server_count))
    await ctx.send(embed=embed)

# 5. Execution logic
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot connection closed.")
