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
        self.db_path = "/app/data/ship_data.db" if os.path.exists("/app/data") else "ship_data.db"
        self._init_db()

    def _init_db(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS ship_users (user_id INTEGER PRIMARY KEY, spouse_id INTEGER, marriage_date TEXT)")

    async def cog_check(self, ctx):
        if hasattr(__main__, "PREMIUM_GUILDS"):
            guild_id = str(ctx.guild.id)
            guild_data = __main__.PREMIUM_GUILDS.get(guild_id, {})
            if guild_data.get(self.module_name):
                return True
        await ctx.send("⚔️ **ARENA LICENSE REQUIRED.**")
        return False

    async def generate_visual(self, u1_url, u2_url, percent):
        """GROUND ZERO ENGINE: Small Square Canvas + 350pt Font = Massive Result."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    img1 = Image.open(io.BytesIO(await r1.read())).convert("RGBA")
                    img2 = Image.open(io.BytesIO(await r2.read())).convert("RGBA")

            # 1. Square Canvas (Forces the font to look giant)
            size = 600
            canvas = Image.new("RGBA", (size, size), (25, 25, 25, 255))
            draw = ImageDraw.Draw(canvas)

            # 2. Avatars (Placed as a background layer)
            av_size = 280
            img1 = ImageOps.fit(img1, (av_size, av_size))
            img2 = ImageOps.fit(img2, (av_size, av_size))
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, av_size, av_size), fill=255)

            canvas.paste(img1, (10, 160), mask)
            canvas.paste(img2, (310, 160), mask)

            # 3. Titanic Score Layer (350pt Scale)
            score_txt = f"{percent}%"
            score_layer = Image.new("RGBA", (size, size), (0,0,0,0))
            s_draw = ImageDraw.Draw(score_layer)
            
            font_paths = ["arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
            font = None
            for p in font_paths:
                try:
                    font = ImageFont.truetype(p, 350)
                    break
                except: continue
            if not font: font = ImageFont.load_default()

            # Massive stroke makes the numbers cut through the avatars
            s_draw.text((size // 2, size // 2), score_txt, fill=(255, 255, 255, 255), 
                        anchor="mm", font=font, stroke_width=15, stroke_fill=(0, 0, 0, 255))

            # 4. Final Composite
            final_output = Image.alpha_composite(canvas, score_layer)

            buf = io.BytesIO()
            final_output.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Ground Zero Error: {e}")
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
