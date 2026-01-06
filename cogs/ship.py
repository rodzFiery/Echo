import discord
from discord.ext import commands
import random
import io
import aiohttp
import os
import sqlite3
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import __main__

class ArenaShip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module_name = "ship"
        self.db_path = "/app/data/ship_data.db" if os.path.exists("/app/data") else "ship_data.db"
        self._init_db()

        # Premium Professional Lexicon
        self.lexicon = {
            "sad": ["Of all the lies humans tell, 'I love you' is my favourite. 😏", "The Arena is silent. No synergy found."],
            "low": ["Recruits in training. A spark exists, but it's cold.", "Lukewarm energy detected in the pits."],
            "medium": ["The crowd is starting to roar. Something is brewing.", "Arena tension is rising between you two."],
            "sexual": ["🔥 **PIT FRICTION.** Primal desire is clouding the Arena.", "69% Sync - A perfect exhibition of heat."],
            "high": ["Legendary Duo. You have conquered the pits and claimed each other.", "Blood-Bound obsession. Unstoppable."],
            "love": ["👑 **IMPERIAL DYNASTY.** Two souls, one unbreakable flame.", "The Great Flame burns eternal for you."]
        }

    def _init_db(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS ship_users (user_id INTEGER PRIMARY KEY, spouse_id INTEGER, marriage_date TEXT)")

    async def cog_check(self, ctx):
        guild_id = str(ctx.guild.id)
        if hasattr(__main__, "PREMIUM_GUILDS"):
            guild_data = __main__.PREMIUM_GUILDS.get(guild_id, {})
            expiry = guild_data.get(self.module_name)
            if expiry and float(expiry) > datetime.now(timezone.utc).timestamp():
                return True
        await ctx.send("⚔️ **ARENA LICENSE REQUIRED.** Type `!premium` to unlock the professional Ship module.")
        return False

    async def generate_pro_visual(self, u1_url, u2_url, percent):
        """High-end Web Design Visualizer based on the reference image."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    if r1.status != 200 or r2.status != 200: return None
                    img1 = Image.open(io.BytesIO(await r1.read())).convert("RGBA")
                    img2 = Image.open(io.BytesIO(await r2.read())).convert("RGBA")

            # --- CANVAS CONFIGURATION ---
            width, height = 1200, 550
            pink_accent = (255, 45, 85) # Vibrant Pink from image
            bg_color = (35, 39, 42, 255) # Discord Darker Grey
            canvas = Image.new("RGBA", (width, height), bg_color)
            draw = ImageDraw.Draw(canvas)

            # 1. LEFT ACCENT BAR
            draw.rectangle([0, 0, 15, height], fill=pink_accent)

            # 2. AVATAR PRO-PROCESSING
            av_size = 480
            # Rounding mask
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, av_size, av_size], radius=80, fill=255)
            
            img1 = ImageOps.fit(img1, (av_size, av_size)).convert("RGBA")
            img2 = ImageOps.fit(img2, (av_size, av_size)).convert("RGBA")
            img1.putalpha(mask)
            img2.putalpha(mask)

            # 3. CENTRAL METER DESIGN (The "Split" Bar)
            meter_w, meter_h = 130, 480
            meter_x = (width // 2) - (meter_w // 2)
            meter_y = 35
            
            # Meter Background
            draw.rectangle([meter_x, meter_y, meter_x + meter_w, meter_y + meter_h], fill=(20, 20, 20))
            
            # Meter Fill (Pink)
            fill_h = (percent / 100) * meter_h
            draw.rectangle([meter_x, (meter_y + meter_h) - fill_h, meter_x + meter_w, meter_y + meter_h], fill=pink_accent)

            # 4. TITANIC SCORE TYPOGRAPHY
            font_paths = ["arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
            # Colossal font size for the "Web Designer" look
            font = next((ImageFont.truetype(p, 110) for p in font_paths if os.path.exists(p)), ImageFont.load_default())

            score_txt = f"{percent}%"
            # Centered on the meter line
            text_x, text_y = width // 2, height // 2
            
            # Massive Shadow for Depth
            draw.text((text_x + 5, text_y + 5), score_txt, fill=(0, 0, 0, 150), anchor="mm", font=font)
            # Main White Text
            draw.text((text_x, text_y), score_txt, fill=(255, 255, 255), anchor="mm", font=font, stroke_width=2, stroke_fill=(255,255,255))

            # 5. COMPOSITING THE FINAL IMAGE
            canvas.paste(img1, (50, 35), img1)
            canvas.paste(img2, (width - av_size - 50, 35), img2)

            # 6. EXPORT
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Professional Engine Error: {e}")
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, u1: discord.Member, u2: discord.Member = None):
        """The Complete Amazing Ship Command"""
        if u2 is None: u2, u1 = u1, ctx.author
        
        # Consistent Daily Rng
        seed = f"{min(u1.id, u2.id)}{max(u1.id, u2.id)}{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        random.seed(seed)
        pct = random.randint(0, 100)
        random.seed()

        tier = "love" if pct == 100 else "high" if pct > 80 else "sexual" if pct > 65 else "medium" if pct > 35 else "low" if pct > 15 else "sad"
        desc = random.choice(self.lexicon[tier]).format(u1=u1.display_name, u2=u2.display_name)

        async with ctx.typing():
            img = await self.generate_pro_visual(u1.display_avatar.url, u2.display_avatar.url, pct)
            if img:
                # Professional Embed matching the Image Accent
                embed = discord.Embed(title="❤️ Shipped off & off!", color=0xFF2D55)
                embed.description = f"### {desc}\n"
                
                # Mentions at the top like the screenshot
                await ctx.send(f"{u1.mention} {u2.mention}")

                file = discord.File(fp=img, filename="ship_pro.png")
                embed.set_image(url="attachment://ship_pro.png")
                embed.set_footer(text="🔄 Lies? Reroll to try for a better score!", icon_url="https://cdn-icons-png.flaticon.com/512/1077/1077035.png")
                
                await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(ArenaShip(bot))
