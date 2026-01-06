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
        """TITANIC ENGINE: High-density square canvas + 500pt font scaling."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    img1 = Image.open(io.BytesIO(await r1.read())).convert("RGBA")
                    img2 = Image.open(io.BytesIO(await r2.read())).convert("RGBA")

            # 1. Square Canvas (600x600 forces the font to appear huge)
            size = 600
            canvas = Image.new("RGBA", (size, size), (20, 20, 20, 255))
            
            # 2. Avatars (Background Layer)
            av_size = 300
            img1 = ImageOps.fit(img1, (av_size, av_size))
            img2 = ImageOps.fit(img2, (av_size, av_size))
            
            # Simple circular mask
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, av_size, av_size), fill=255)

            # Paste Avatars behind the text
            canvas.paste(img1, (0, 150), mask)
            canvas.paste(img2, (300, 150), mask)

            # 3. TITANIC FONT SCALE (500pt)
            score_txt = f"{percent}%"
            # Create a dedicated layer for the gargantuan text
            txt_layer = Image.new("RGBA", (size, size), (0,0,0,0))
            t_draw = ImageDraw.Draw(txt_layer)
            
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "arial.ttf",
                "DejaVuSans-Bold.ttf"
            ]
            
            font = None
            for p in font_paths:
                try:
                    font = ImageFont.truetype(p, 500) # GARGANTUAN SCALE
                    break
                except: continue
            
            if not font: font = ImageFont.load_default()

            # 4. RENDER GIANT SCORE
            # Huge black stroke (20px) ensures readability against the avatars
            t_draw.text((size // 2, size // 2), score_txt, fill=(255, 255, 255, 255), 
                        anchor="mm", font=font, stroke_width=20, stroke_fill=(0, 0, 0, 255))

            # 5. Final Composite
            final_output = Image.alpha_composite(canvas, txt_layer)

            buf = io.BytesIO()
            final_output.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Titanic Fix Error: {e}")
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
