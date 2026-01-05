import discord
from discord.ext import commands
import random
import io
import aiohttp
import sys
import os
import sqlite3
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import __main__

class ArenaShip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module_name = "ship"
        self.AUDIT_CHANNEL_ID = 1438810509322223677
        self.db_path = "/app/data/ship_data.db" if os.path.exists("/app/data") else "ship_data.db"
        self._init_db()

        # Modern Arena Lexicon
        self.lexicon = {
            "sad": ["The Arena is silent. {u1} and {u2} have no synergy.", "Zero heat. The Emperor is bored."],
            "low": ["Recruits in training. {u1} and {u2} barely spark.", "Lukewarm synergy in the pits."],
            "medium": ["The crowd stirs. A spark forms between {u1} and {u2}.", "Arena tension is rising."],
            "sexual": ["🔥 **PIT FRICTION.**Primal desire detected.", "69% Sync - The perfect exhibition."],
            "high": ["Legendary Duo. Conquered the pits together.", "Blood-Bound obsession."],
            "love": ["👑 **IMPERIAL DYNASTY.** Souls merged forever.", "The Great Flame burns eternal."]
        }

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS ship_users (user_id INTEGER PRIMARY KEY, spouse_id INTEGER, marriage_date TEXT)")

    async def cog_check(self, ctx):
        guild_id = str(ctx.guild.id)
        if hasattr(__main__, "PREMIUM_GUILDS"):
            guild_data = __main__.PREMIUM_GUILDS.get(guild_id, {})
            expiry = guild_data.get(self.module_name)
            if expiry and float(expiry) > datetime.now(timezone.utc).timestamp():
                return True
        await ctx.send("⚔️ **ARENA LICENSE REQUIRED.** Type `!premium` to unlock.")
        return False

    async def generate_web_ui(self, u1_url, u2_url, percent):
        """Web-style UI: Rounded Cards + Integrated Bar"""
        async with aiohttp.ClientSession() as session:
            async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                img1 = Image.open(io.BytesIO(await r1.read())).convert("RGBA")
                img2 = Image.open(io.BytesIO(await r2.read())).convert("RGBA")

        # 1. Setup Canvas (1000x450 for that sleek card look)
        canvas = Image.new("RGBA", (1000, 450), (30, 31, 34, 255)) 
        draw = ImageDraw.Draw(canvas)
        
        # 2. Process Avatars (Rounded Corners)
        av_size = 400
        mask = Image.new("L", (av_size, av_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, av_size, av_size], radius=40, fill=255)
        
        img1 = ImageOps.fit(img1, (av_size, av_size)).convert("RGBA")
        img2 = ImageOps.fit(img2, (av_size, av_size)).convert("RGBA")
        img1.putalpha(mask)
        img2.putalpha(mask)

        # 3. Dynamic Heat Color
        bar_color = (255, 45, 85) if percent > 60 else (255, 215, 0) if percent > 30 else (150, 150, 150)

        # 4. The Center Meter (Web Design Style)
        meter_x, meter_y, meter_w, meter_h = 450, 50, 100, 350
        # Background of bar
        draw.rectangle([meter_x, meter_y, meter_x + meter_w, meter_y + meter_h], fill=(15, 15, 15))
        # Fill of bar
        fill_h = (percent / 100) * meter_h
        draw.rectangle([meter_x, (meter_y + meter_h) - fill_h, meter_x + meter_w, meter_y + meter_h], fill=bar_color)

        # 5. Titanic Typography (Centered on the bar)
        try:
            font = ImageFont.truetype("arial.ttf", 65)
        except:
            font = ImageFont.load_default()

        score_txt = f"{percent}%"
        # Draw text with high contrast directly in the center
        draw.text((500, 225), score_txt, fill=(255, 255, 255), anchor="mm", font=font, stroke_width=4, stroke_fill=(0,0,0))

        # 6. Final Paste
        canvas.paste(img1, (25, 25), img1)
        canvas.paste(img2, (575, 25), img2)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf

    @commands.command(name="ship")
    async def ship(self, ctx, u1: discord.Member, u2: discord.Member = None):
        if u2 is None: u2, u1 = u1, ctx.author
        
        # Daily Seed Logic
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        random.seed(f"{min(u1.id, u2.id)}{max(u1.id, u2.id)}{today}")
        pct = random.randint(0, 100)
        random.seed()

        tier = "love" if pct == 100 else "high" if pct > 75 else "sexual" if pct > 60 else "medium" if pct > 30 else "low" if pct > 10 else "sad"
        desc = random.choice(self.lexicon[tier]).format(u1=u1.display_name, u2=u2.display_name)

        async with ctx.typing():
            img = await self.generate_web_ui(u1.display_avatar.url, u2.display_avatar.url, pct)
            embed = discord.Embed(title="❤️ Shipped off & off!", description=f"**{u1.mention} & {u2.mention}**\n*{desc}*", color=0xFF2D55)
            file = discord.File(img, filename="ship.png")
            embed.set_image(url="attachment://ship.png")
            embed.set_footer(text="Lies? Reroll tomorrow for a better score! 🫦")
            await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(ArenaShip(bot))
