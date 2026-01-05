import discord
import os
import asyncio
import io
import aiohttp
import json
from datetime import datetime, timezone
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw

# 1. Setup & Secrets
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# Add IDs of servers that paid the 2.50 USD here
PREMIUM_GUILDS = [123456789012345678] 

if TOKEN is None:
    print("ERROR: DISCORD_TOKEN not found.")
    exit(1)

# 2. Intents & Bot Initialization
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.change_presence(activity=discord.Game(name="!ask | !invite"))

bot = MyBot()

# --- UTILS ---
HISTORY_FILE = "ask_history.json"

def fiery_embed(title, description, color=0xff4500):
    return discord.Embed(title=title, description=description, color=color)

def log_ask_event(requester, target, intent, status):
    data = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try: data = json.load(f)
            except: data = []
    data.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "requester": str(requester),
        "target": str(target),
        "intent": intent,
        "status": status
    })
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- IMAGE ENGINE (PREMIUM ONLY) ---
async def create_premium_lobby(u1_url, u2_url):
    try:
        canvas = Image.new("RGBA", (1200, 600), (15, 0, 8, 255))
        draw = ImageDraw.Draw(canvas)
        async with aiohttp.ClientSession() as session:
            async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                p1, p2 = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())
        
        av1 = Image.open(p1).convert("RGBA").resize((350, 350))
        av2 = Image.open(p2).convert("RGBA").resize((350, 350))
        
        # Glow Effect
        for i in range(15, 0, -1):
            alpha = int(255 * (1 - i/15))
            draw.rectangle([100-i, 120-i, 100+350+i, 120+350+i], outline=(255, 20, 147, alpha), width=2)
            draw.rectangle([750-i, 120-i, 750+350+i, 120+350+i], outline=(255, 0, 0, alpha), width=2)
        
        canvas.paste(av1, (100, 120), av1)
        canvas.paste(av2, (750, 120), av2)
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except: return None

# --- HYBRID ASK COMMAND ---
@bot.command(name="ask")
async def ask(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.send("❌ You cannot ask yourself.")

    is_premium = ctx.guild.id in PREMIUM_GUILDS
    
    # Visual Logic Gate
    if is_premium:
        img = await create_premium_lobby(ctx.author.display_avatar.url, member.display_avatar.url)
        file = discord.File(img, filename="ask.png")
        embed = fiery_embed("💎 PREMIUM DM REQUEST 💎", f"{ctx.author.mention} vs {member.mention}")
        embed.set_image(url="attachment://ask.png")
    else:
        file = None
        embed = fiery_embed("🔥 BASIC DM REQUEST 🔥", f"{ctx.author.mention} wants to talk to {member.mention}.\n\n*Upgrade to Premium for custom visual lobbies!*")

    class InitialView(discord.ui.View):
        def __init__(self, r, t):
            super().__init__(timeout=120); self.r, self.t = r, t
        @discord.ui.button(label="Ask to DM", style=discord.ButtonStyle.primary, emoji="📩")
        async def dm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.r.id: return
            options = [discord.SelectOption(label="SFW"), discord.SelectOption(label="NSFW")]
            select = discord.ui.Select(options=options)
            async def callback(i: discord.Interaction):
                intent = select.values[0]
                class RecView(discord.ui.View):
                    def __init__(self, r, t, it):
                        super().__init__(timeout=300); self.r, self.t, self.it = r, t, it
                    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
                    async def acc(self, i, b):
                        if i.user.id != self.t.id: return
                        log_ask_event(self.r, self.t, self.it, "Accepted")
                        await i.response.send_message(f"✅ {self.t.mention} accepted!")
                    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
                    async def den(self, i, b):
                        if i.user.id != self.t.id: return
                        log_ask_event(self.r, self.t, self.it, "Denied")
                        await i.response.send_message(f"❌ {self.t.mention} denied.")
                await i.response.send_message(content=self.t.mention, view=RecView(self.r, self.t, intent))
            select.callback = callback
            v = discord.ui.View(); v.add_item(select)
            await interaction.response.send_message("Select intent:", view=v, ephemeral=True)

    await ctx.send(file=file, embed=embed, view=InitialView(ctx.author, member))

# --- ADMIN & INVITE ---
@bot.command()
@commands.has_permissions(administrator=True)
async def adminask(ctx):
    if ctx.guild.id not in PREMIUM_GUILDS:
        return await ctx.send("🚫 **Admin History is a Premium Feature.**\nContact support to upgrade.")
    # (Insert the history selection logic here as coded previously)
    await ctx.send("Premium History Access Granted. (Logic loading...)")

@bot.command()
async def invite(ctx):
    link = discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(administrator=True))
    await ctx.send(f"Add me: {link}")

# 5. Launch
async def main():
    async with bot: await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
