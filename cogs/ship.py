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

        self.lexicon = {
            "sad": ["The Arena is silent. {u1} and {u2} have no synergy.", "Zero heat."],
            "low": ["Recruits in training. {u1} and {u2} barely spark."],
            "medium": ["The crowd stirs. A spark forms between {u1} and {u2}."],
            "sexual": ["🔥 **PIT FRICTION.** Primal desire detected."],
            "high": ["Legendary Duo. Conquered the pits together."],
            "love": ["👑 **IMPERIAL DYNASTY.** Souls merged forever."]
        }

    def _init_db(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS ship_users (user_id INTEGER PRIMARY KEY, spouse_id INTEGER, marriage_date TEXT)")

    def get_marriage(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("SELECT * FROM ship_users WHERE user_id = ?", (user_id,)).fetchone()

    async def cog_check(self, ctx):
        guild_id = str(ctx.guild.id)
        if hasattr(__main__, "PREMIUM_GUILDS"):
            guild_data = __main__.PREMIUM_GUILDS.get(guild_id, {})
            expiry = guild_data.get(self.module_name)
            if expiry and float(expiry) > datetime.now(timezone.utc).timestamp():
                return True
        await ctx.send("⚔️ **ARENA LICENSE REQUIRED.**")
        return False

    async def generate_visual(self, u1_url, u2_url, percent):
        """GROUND ZERO ENGINE: Small canvas + Massive font = Giant Score."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    img1 = Image.open(io.BytesIO(await r1.read())).convert("RGBA")
                    img2 = Image.open(io.BytesIO(await r2.read())).convert("RGBA")

            # 1. Canvas Configuration (Compact 800x400)
            # A smaller canvas makes the font appear much larger
            width, height = 800, 400
            canvas = Image.new("RGBA", (width, height), (32, 34, 37, 255))
            draw = ImageDraw.Draw(canvas)

            # 2. Avatar Formatting (Half-width circles)
            av_size = 320
            img1 = ImageOps.fit(img1, (av_size, av_size))
            img2 = ImageOps.fit(img2, (av_size, av_size))
            
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, av_size, av_size), fill=255)

            # 3. Paste Avatars
            canvas.paste(img1, (40, 40), mask)
            canvas.paste(img2, (width - av_size - 40, 40), mask)

            # 4. TITANIC FONT SCALE
            # 300pt on a 400px height canvas is MASSIVE
            font_paths = ["arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
            font = None
            for p in font_paths:
                try:
                    font = ImageFont.truetype(p, 300)
                    break
                except: continue
            if not font: font = ImageFont.load_default()

            # 5. RENDER GIANT SCORE
            score_txt = f"{percent}%"
            # Create a separate layer to handle transparency/blending
            txt_layer = Image.new("RGBA", (width, height), (0,0,0,0))
            t_draw = ImageDraw.Draw(txt_layer)
            
            # Draw with massive black stroke for legibility
            t_draw.text((width//2, height//2), score_txt, fill=(255, 255, 255, 255), 
                        anchor="mm", font=font, stroke_width=12, stroke_fill=(0, 0, 0, 255))

            # 6. Final Composite
            canvas = Image.alpha_composite(canvas, txt_layer)

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Error: {e}")
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, u1: discord.Member, u2: discord.Member = None):
        if u2 is None: u2, u1 = u1, ctx.author
        
        seed = f"{min(u1.id, u2.id)}{max(u1.id, u2.id)}{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        random.seed(seed)
        pct = random.randint(0, 100)
        random.seed()

        tier = "love" if pct == 100 else "high" if pct > 75 else "sexual" if pct > 60 else "medium" if pct > 30 else "low" if pct > 10 else "sad"
        desc = random.choice(self.lexicon[tier]).format(u1=u1.display_name, u2=u2.display_name)

        async with ctx.typing():
            img = await self.generate_visual(u1.display_avatar.url, u2.display_avatar.url, pct)
            if img:
                file = discord.File(fp=img, filename="ship.png")
                embed = discord.Embed(title="❤️ Arena Sync", description=f"**{pct}%**\n{desc}", color=0xE91E63)
                embed.set_image(url="attachment://ship.png")
                await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(ArenaShip(bot))
