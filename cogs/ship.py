import discord
from discord.ext import commands
import random
import io
import aiohttp
import sys
import os
import sqlite3
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
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
            "sexual": ["🔥 **PIT FRICTION.** Primal desire detected.", "69% Sync - The perfect exhibition."],
            "high": ["Legendary Duo. Conquered the pits together.", "Blood-Bound obsession."],
            "love": ["👑 **IMPERIAL DYNASTY.** Souls merged forever.", "The Great Flame burns eternal."]
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
        await ctx.send("⚔️ **ARENA LICENSE REQUIRED.** Type `!premium` to unlock.")
        return False

    async def generate_web_ui(self, u1_url, u2_url, percent):
        """Web-style UI: Rounded Cards + Integrated Bar with robust font loading."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    if r1.status != 200 or r2.status != 200:
                        return None
                    img1_data = io.BytesIO(await r1.read())
                    img2_data = io.BytesIO(await r2.read())
                    img1 = Image.open(img1_data).convert("RGBA")
                    img2 = Image.open(img2_data).convert("RGBA")

            # 1. Setup Canvas (1000x450)
            canvas = Image.new("RGBA", (1000, 450), (30, 31, 34, 255)) 
            draw = ImageDraw.Draw(canvas)
            
            # 2. Process Avatars (Rounded Corners)
            av_size = 400
            mask = Image.new("L", (av_size, av_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([0, 0, av_size, av_size], radius=40, fill=255)
            
            img1 = ImageOps.fit(img1, (av_size, av_size)).convert("RGBA")
            img2 = ImageOps.fit(img2, (av_size, av_size)).convert("RGBA")
            img1.putalpha(mask)
            img2.putalpha(mask)

            # 3. Dynamic Heat Color
            bar_color = (255, 45, 85) if percent > 60 else (255, 215, 0) if percent > 30 else (150, 150, 150)

            # 4. The Center Meter
            meter_x, meter_y, meter_w, meter_h = 450, 50, 100, 350
            draw.rectangle([meter_x, meter_y, meter_x + meter_w, meter_y + meter_h], fill=(15, 15, 15))
            fill_h = (percent / 100) * meter_h
            draw.rectangle([meter_x, (meter_y + meter_h) - fill_h, meter_x + meter_w, meter_y + meter_h], fill=bar_color)

            # 5. FONT WORKAROUND (Critical Fix)
            font_paths = [
                "arial.ttf", 
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "DejaVuSans-Bold.ttf"
            ]
            font = None
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, 65)
                    break
                except:
                    continue
            if font is None:
                font = ImageFont.load_default()

            score_txt = f"{percent}%"
            draw.text((500, 225), score_txt, fill=(255, 255, 255), anchor="mm", font=font, stroke_width=4, stroke_fill=(0,0,0))

            # 6. Final Paste
            canvas.paste(img1, (25, 25), img1)
            canvas.paste(img2, (575, 25), img2)

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Image Generation Error: {e}")
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, u1: discord.Member, u2: discord.Member = None):
        if u2 is None: u2, u1 = u1, ctx.author
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seed_str = f"{min(u1.id, u2.id)}{max(u1.id, u2.id)}{today}"
        random.seed(seed_str)
        pct = random.randint(0, 100)
        random.seed()

        tier = "love" if pct == 100 else "high" if pct > 75 else "sexual" if pct > 60 else "medium" if pct > 30 else "low" if pct > 10 else "sad"
        desc = random.choice(self.lexicon[tier]).format(u1=u1.display_name, u2=u2.display_name)

        async with ctx.typing():
            try:
                img = await self.generate_web_ui(u1.display_avatar.url, u2.display_avatar.url, pct)
                if img is None:
                    return await ctx.send("❌ Error generating ship image. Please check logs.")
                
                embed = discord.Embed(title="❤️ Shipped off & off!", description=f"**{u1.mention} & {u2.mention}**\n*{desc}*", color=0xFF2D55)
                file = discord.File(fp=img, filename="ship.png")
                embed.set_image(url="attachment://ship.png")
                embed.set_footer(text="Lies? Reroll tomorrow for a better score! 🫦")
                await ctx.send(file=file, embed=embed)
            except Exception as e:
                print(f"Command Error: {e}")
                await ctx.send("❌ An unexpected error occurred.")

async def setup(bot):
    await bot.add_cog(ArenaShip(bot))
