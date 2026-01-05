import discord
import os
import asyncio
import io
import aiohttp
import json
import sys
from datetime import datetime, timezone, timedelta
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageOps, ImageFilter

# 1. SETUP & SECRETS
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TOPGG_TOKEN = os.getenv('TOPGG_TOKEN')
PAYPAL_EMAIL = 'YOUR_PAYPAL_EMAIL'  # Replace this with your PayPal email

# Verification for Railway
if TOKEN is None:
    print("ERROR: DISCORD_TOKEN not found in the environment.")
    exit(1)

# 2. INTENTS & INITIALIZATION
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        print("--- Initializing Systems ---")
        # Persistent Premium Loading
        global PREMIUM_GUILDS
        if os.path.exists("premium_guilds.json"):
            with open("premium_guilds.json", "r") as f:
                PREMIUM_GUILDS = json.load(f)
        else:
            PREMIUM_GUILDS = []
        print(f"Loaded {len(PREMIUM_GUILDS)} Premium Servers.")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.change_presence(activity=discord.Game(name="!ask | !invite"))
        print('Bot is online and ready for Top.gg.')

    async def on_connect(self):
        print("Bridge established with Railway environment.")

    async def on_guild_join(self, guild):
        print(f"New server joined: {guild.name}")

bot = MyBot()

# 3. UTILS & DATABASE LOGIC
HISTORY_FILE = "ask_history.json"
PREMIUM_GUILDS = []

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

# 4. IMAGE ENGINE (PREMIUM FEATURE)
async def create_premium_lobby(u1_url, u2_url):
    try:
        canvas_width, canvas_height = 1200, 600
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (15, 0, 8, 255))
        draw = ImageDraw.Draw(canvas)

        async with aiohttp.ClientSession() as session:
            async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                p1_data = io.BytesIO(await r1.read())
                p2_data = io.BytesIO(await r2.read())

        av_size = 350
        av1 = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
        av2 = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

        def draw_glow(draw_obj, pos, size, color):
            for i in range(15, 0, -1):
                alpha = int(255 * (1 - i/15))
                draw_obj.rectangle([pos[0]-i, pos[1]-i, pos[0]+size+i, pos[1]+size+i], outline=(*color, alpha), width=2)

        draw_glow(draw, (100, 120), av_size, (255, 20, 147)) 
        draw_glow(draw, (750, 120), av_size, (255, 0, 0))   

        canvas.paste(av1, (100, 120), av1)
        canvas.paste(av2, (750, 120), av2)
        draw.text((550, 250), "VS", fill=(255, 0, 0))

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"Visual Error: {e}")
        return None

# 5. CORE COMMANDS (ASK & PREMIUM GATE)
@bot.command(name="ask")
async def ask(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.send("❌ You cannot ask yourself.")

    is_premium = ctx.guild.id in PREMIUM_GUILDS
    
    if is_premium:
        img = await create_premium_lobby(ctx.author.display_avatar.url, member.display_avatar.url)
        file = discord.File(img, filename="ask.png")
        embed = fiery_embed("💎 PREMIUM DM REQUEST 💎", f"{ctx.author.mention} is signaling {member.mention}.")
        embed.set_image(url="attachment://ask.png")
    else:
        file = None
        embed = fiery_embed("🔥 BASIC DM REQUEST 🔥", f"{ctx.author.mention} wants to talk to {member.mention}.\n\n*Upgrade to Premium (!buy) for custom visual lobbies!*")

    class InitialView(discord.ui.View):
        def __init__(self, req, tar):
            super().__init__(timeout=120)
            self.req, self.tar = req, tar

        @discord.ui.button(label="Ask to DM", style=discord.ButtonStyle.primary, emoji="📩")
        async def dm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.req.id: return
            
            options = [
                discord.SelectOption(label="SFW", emoji="🛡️"),
                discord.SelectOption(label="NSFW", emoji="🔞"),
                discord.SelectOption(label="Flirting", emoji="🫦"),
                discord.SelectOption(label="Casual Chat", emoji="💬")
            ]
            select = discord.ui.Select(placeholder="Nature of the DM", options=options)

            async def select_callback(sel_inter: discord.Interaction):
                intent = select.values[0]
                final_emb = fiery_embed("📩 INCOMING DM REQUEST", f"{self.tar.mention}, {self.req.mention} wants to connect for: **{intent}**")
                
                class RecipientView(discord.ui.View):
                    def __init__(self, r, t, it):
                        super().__init__(timeout=300); self.r, self.t, self.it = r, t, it
                    
                    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="🫦")
                    async def acc(self, i, b):
                        if i.user.id != self.t.id: return
                        log_ask_event(self.r, self.t, self.it, "Accepted")
                        await i.response.send_message(embed=fiery_embed("💖 ACCEPTED", f"{self.r.mention}, your request was accepted!"))
                    
                    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, emoji="🥀")
                    async def den(self, i, b):
                        if i.user.id != self.t.id: return
                        log_ask_event(self.r, self.t, self.it, "Denied")
                        await i.response.send_message(embed=fiery_embed("🥀 DENIED", f"{self.r.mention}, your request was rejected."))
                
                await sel_inter.response.send_message(content=self.tar.mention, embed=final_emb, view=RecipientView(self.req, self.tar, intent))
            
            select.callback = select_callback
            v = discord.ui.View(); v.add_item(select)
            await interaction.response.send_message("Define your intent:", view=v, ephemeral=True)

    await ctx.send(file=file, embed=embed, view=InitialView(ctx.author, member))

# 6. ADMIN & PAYMENT COMMANDS
@bot.command(name="adminask")
@commands.has_permissions(administrator=True)
async def adminask(ctx):
    if ctx.guild.id not in PREMIUM_GUILDS:
        return await ctx.send("🚫 **Admin History is a Premium Feature.** Type `!buy` to upgrade.")
    
    embed = fiery_embed("📊 ASK HISTORY PANEL", "Select a timeframe to view the logs.")
    
    class HistoryView(discord.ui.View):
        @discord.ui.select(placeholder="Choose Timeframe", options=[
            discord.SelectOption(label="Since Ever", value="0"),
            discord.SelectOption(label="Last 1 Month", value="30"),
            discord.SelectOption(label="Last 3 Months", value="90"),
            discord.SelectOption(label="Last 6 Months", value="180")
        ])
        async def select_time(self, interaction: discord.Interaction, select: discord.ui.Select):
            days = int(select.values[0])
            if not os.path.exists(HISTORY_FILE):
                return await interaction.response.send_message("No logs found.", ephemeral=True)
            
            with open(HISTORY_FILE, "r") as f:
                logs = json.load(f)
            
            now = datetime.now(timezone.utc)
            filtered = [e for e in logs if days == 0 or (now - datetime.fromisoformat(e['timestamp'])).days <= days]
            
            res = "\n".join([f"• {e['requester']} ➡️ {e['target']} [{e['status']}]" for e in filtered[-10:]])
            report = fiery_embed(f"History: {select.values[0]} Days", f"Total: {len(filtered)}\n\nRecent:\n{res if res else 'None'}")
            await interaction.response.send_message(embed=report, ephemeral=True)

    await ctx.send(embed=embed, view=HistoryView())

@bot.command()
@commands.has_permissions(administrator=True)
async def buy(ctx):
    paypal_link = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={PAYPAL_EMAIL}&amount=2.50&currency_code=USD&item_name=Premium_Server_{ctx.guild.id}&custom={ctx.guild.id}"
    embed = fiery_embed("💎 PREMIUM UPGRADE", f"Click [**HERE**]({paypal_link}) to pay $2.50 via PayPal.\nInclude Server ID: `{ctx.guild.id}` in notes.")
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def activate(ctx, guild_id: int):
    """Owner-only command to manually activate premium after checking PayPal."""
    if guild_id not in PREMIUM_GUILDS:
        PREMIUM_GUILDS.append(guild_id)
        with open("premium_guilds.json", "w") as f:
            json.dump(PREMIUM_GUILDS, f)
        await ctx.send(f"✅ Guild {guild_id} is now Premium!")

@bot.command()
async def invite(ctx):
    link = discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(administrator=True))
    await ctx.send(f"Add me to your server: {link}")

@bot.command()
async def stats(ctx):
    embed = discord.Embed(title="Bot Metrics", color=discord.Color.green())
    embed.add_field(name="Servers", value=str(len(bot.guilds)))
    await ctx.send(embed=embed)

# 7. EXECUTION
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot offline.")
