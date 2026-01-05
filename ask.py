import discord
import os
import asyncio
import io
import aiohttp
import sys
import json
from datetime import datetime, timezone, timedelta
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageOps, ImageFilter

# 1. Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    print("ERROR: DISCORD_TOKEN not found.")
    exit(1)

# 2. Define Bot Intents
intents = discord.Intents.default()
intents.message_content = True  
intents.members = True          

# Helper function for embeds
def fiery_embed(title, description, color=0xff4500):
    return discord.Embed(title=title, description=description, color=color)

# 3. History Logging System (NEW ADDITION)
HISTORY_FILE = "ask_history.json"

def log_ask_event(requester, target, intent, status):
    data = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try: data = json.load(f)
            except: data = []
    
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "requester": str(requester),
        "target": str(target),
        "intent": intent,
        "status": status
    }
    data.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# 4. Initialize the Bot
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.change_presence(activity=discord.Game(name="!ask | !adminask"))

bot = MyBot()

# --- Integrated DungeonAsk Logic ---

async def create_ask_lobby(u1_url, u2_url, title="DM REQUEST"):
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
        print(f"Ask Visual Error: {e}"); return None

@bot.command(name="ask")
async def ask(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.send("❌ You can't ask to DM yourself.")

    img = await create_ask_lobby(ctx.author.display_avatar.url, member.display_avatar.url)
    file = discord.File(img, filename="ask.png")
    embed = fiery_embed("🔞 ASK TO DM ALERT 🔞", f"{ctx.author.mention} is signaling {member.mention}.")
    embed.set_image(url="attachment://ask.png")

    class InitialView(discord.ui.View):
        def __init__(self, req, tar):
            super().__init__(timeout=120)
            self.req, self.tar = req, tar

        @discord.ui.button(label="Ask to DM", style=discord.ButtonStyle.primary, emoji="📩")
        async def dm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.req.id: return
            options = [discord.SelectOption(label="SFW", emoji="🛡️"), discord.SelectOption(label="NSFW", emoji="🔞")]
            select = discord.ui.Select(placeholder="Nature of the DM", options=options)

            async def select_callback(sel_inter: discord.Interaction):
                intent = select.values[0]
                final_emb = fiery_embed("📩 INCOMING DM REQUEST", f"{self.tar.mention}, {self.req.mention} wants to connect for: **{intent}**")
                
                class RecipientView(discord.ui.View):
                    def __init__(self, r, t, i):
                        super().__init__(timeout=300); self.r, self.t, self.i = r, t, i
                    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
                    async def acc(self, i, b):
                        if i.user.id != self.t.id: return
                        log_ask_event(self.r, self.t, self.i, "Accepted")
                        await i.response.send_message("✅ DM Accepted.")
                    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
                    async def den(self, i, b):
                        if i.user.id != self.t.id: return
                        log_ask_event(self.r, self.t, self.i, "Denied")
                        await i.response.send_message("❌ DM Denied.")
                
                await sel_inter.response.send_message(content=self.tar.mention, embed=final_emb, view=RecipientView(self.req, self.tar, intent))
            
            select.callback = select_callback
            view = discord.ui.View(); view.add_item(select)
            await interaction.response.send_message("Select intent:", view=view, ephemeral=True)

    await ctx.send(file=file, embed=embed, view=InitialView(ctx.author, member))

# --- NEW ADMIN HISTORY COMMAND ---

@bot.command(name="adminask")
@commands.has_permissions(administrator=True)
async def adminask(ctx):
    """Admin command to view ask history with timeframe selection."""
    embed = fiery_embed("📊 ASK HISTORY PANEL", "Select a timeframe to view the DM request logs.")
    
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
                return await interaction.response.send_message("No history found.", ephemeral=True)
            
            with open(HISTORY_FILE, "r") as f:
                logs = json.load(f)
            
            now = datetime.now(timezone.utc)
            filtered = []
            for entry in logs:
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if days == 0 or (now - entry_time).days <= days:
                    filtered.append(entry)
            
            res = "\n".join([f"• {e['requester']} ➡️ {e['target']} [{e['status']}]" for e in filtered[-10:]])
            report = fiery_embed(f"Results: {select.values[0]} Days", f"**Total Requests Found:** {len(filtered)}\n\n**Recent Activity:**\n{res if res else 'No logs for this period.'}")
            await interaction.response.send_message(embed=report, ephemeral=True)

    await ctx.send(embed=embed, view=HistoryView())

async def main():
    async with bot: await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
