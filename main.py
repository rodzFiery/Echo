import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# 1. Load environment variables for security
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# --- ADDITION: Railway Variable Verification ---
if TOKEN is None:
    print("ERROR: DISCORD_TOKEN not found in the environment.")
    print("If you are on Railway, check the 'Variables' tab.")
    exit(1)
# -----------------------------------------------

# 2. Define Bot Intents (Required for modern Discord bots)
intents = discord.Intents.default()
intents.message_content = True  # Allows bot to read messages if needed
intents.members = True          # Needed for Top.gg tracking usually

# 3. Initialize the Bot Bridge
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )

    # This function acts as the bridge to load all other .py files
    async def setup_hook(self):
        print("--- Connecting to Cogs ---")
        # Ensure the cogs directory exists so the bridge doesn't crash
        if not os.path.exists('./cogs'):
            os.makedirs('./cogs')
            
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Bridge established for: {filename}')
                except Exception as e:
                    print(f'Failed to bridge {filename}: {e}')
        print("--- Bridge Setup Complete ---")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('Ready for Top.gg integration.')

    # --- ADDITION: Connection Event ---
    async def on_connect(self):
        print(f"Bridge successfully pulled the token from the environment.")
    # ----------------------------------

# 4. Execution logic
bot = MyBot()

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot connection closed.")
