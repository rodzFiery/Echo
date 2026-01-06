import discord
from discord.ext import commands
import random
import io
import aiohttp
import os
import sqlite3
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageOps
import __main__

class ArenaShip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module_name = "ship"
        self.db_path = "ship_data.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS ship_users (user_id INTEGER PRIMARY KEY, spouse_id INTEGER, marriage_date TEXT)")

    async def cog_check(self, ctx):
        # Keeps your main.py sync logic intact
        if hasattr(__main__, "PREMIUM_GUILDS"):
            guild_id = str(ctx.guild.id)
            guild_data = __main__.PREMIUM_GUILDS.get(guild_id, {})
            if guild_data.get(self.module_name):
                return True
        await ctx.send("⚔️ **ARENA LICENSE REQUIRED.**")
        return False

    async def generate_visual(self, u1_url, u2_url, percent):
        """TITANIC ENGINE: Max Center Space + Massive Font Scaling."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    img1 = Image.open(io.BytesIO(await r1.read())).convert("RGBA")
                    img2 = Image.open(io.BytesIO(await r2.read())).convert("RGBA")

            # --- 1. CANVAS GEOMETRY ---
            # Shorter width (900) and standard height (450) makes center area look bigger
            width, height = 900, 450
            canvas = Image.new("RGBA", (width, height), (30, 31, 34, 255))
            draw = ImageDraw.Draw(canvas)

            # --- 2. THE METER (MASSIVE STAGE) ---
            # We widen the meter so the numbers have actual room to be big
            meter_w = 260 
            meter_x = (width // 2) - (meter_w // 2)
            
            # Meter Background
            draw.rectangle([meter_x, 0, meter_x + meter_w, height], fill=(15, 15, 15))
            
            # Meter Fill (Vibrant Pink)
            fill_h = (percent / 100) * height
            draw.rectangle([meter_x, height - fill_h, meter_x + meter_w, height], fill=(233, 30, 99))

            # --- 3. TITANIC TYPOGRAPHY (320pt SCALE) ---
            # At 320pt on a 450px canvas, the text is a GIANT.
            font_paths = ["arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
            font = None
            for p in font_paths:
                try:
                    font = ImageFont.truetype(p, 320)
                    break
                except: continue
            if not font: font = ImageFont.load_default()

            # --- 4. RENDER SCORE ---
            score_txt = f"{percent}%"
            score_layer = Image.new("RGBA", (width, height), (0,0,0,0))
            s_draw = ImageDraw.Draw(score_layer)
            
            # Massive High-Visibility Stroke
            s_draw.text((width // 2, height // 2), score_txt, fill=(255, 255, 255, 255), 
                        anchor="mm", font=font, stroke_width=10, stroke_fill=(0, 0, 0, 255))

            # --- 5. AVATAR PLACEMENT ---
            # Scaled down slightly to not fight with the giant numbers
            av_size = 300
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, av_size, av_size], radius=40, fill=255)
            
            img1 = ImageOps.fit(img1, (av_size, av_size)).convert("RGBA")
            img2 = ImageOps.fit(img2, (av_size, av_size)).convert("RGBA")
            
            canvas.paste(img1, (20, 75), mask)
            canvas.paste(img2, (width - av_size - 20, 75), mask)

            # --- 6. FINAL ALPHA MERGE ---
            canvas = Image.alpha_composite(canvas, score_layer)

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Visual Error: {e}")
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, u1: discord.Member, u2: discord.Member = None):
        if u2 is None: u2, u1 = u1, ctx.author
        
        pct = random.randint(0, 100)
        async with ctx.typing():
            img = await self.generate_visual(u1.display_avatar.url, u2.display_avatar.url, pct)
            if img:
                file = discord.File(fp=img, filename="ship.png")
                await ctx.send(file=file)

async def setup(bot):
    await bot.add_cog(ArenaShip(bot))
