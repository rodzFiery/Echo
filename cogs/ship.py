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
        self.AUDIT_CHANNEL_ID = 1438810509322223677
        self.db_path = "/app/data/ship_data.db" if os.path.exists("/app/data") else "ship_data.db"
        self._init_db()

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
        await ctx.send("⚔️ **ARENA LICENSE REQUIRED.** Type `!premium` to unlock.")
        return False

    async def generate_web_ui(self, u1_url, u2_url, percent):
        """Web-style UI: Optimized with Layered Compositing to prevent hanging."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    if r1.status != 200 or r2.status != 200:
                        return None
                    img1_raw = await r1.read()
                    img2_raw = await r2.read()
                    img1 = Image.open(io.BytesIO(img1_raw)).convert("RGBA")
                    img2 = Image.open(io.BytesIO(img2_raw)).convert("RGBA")

            # --- CANVAS CONFIG ---
            width, height = 1000, 450
            canvas = Image.new("RGBA", (width, height), (32, 34, 37, 255)) 
            draw = ImageDraw.Draw(canvas)
            
            # 1. ACCENT
            draw.rectangle([0, 0, 12, height], fill=(233, 30, 99))

            # 2. AVATARS (Processing fit before paste)
            av_size = 410
            img1 = ImageOps.fit(img1, (av_size, av_size))
            img2 = ImageOps.fit(img2, (av_size, av_size))
            
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, av_size, av_size], radius=60, fill=255)

            # 3. THE METER
            meter_w = 120
            meter_x = (width // 2) - (meter_w // 2)
            # Bg
            draw.rectangle([meter_x, 0, meter_x + meter_w, height], fill=(15, 15, 15))
            # Fill
            fill_h = (percent / 100) * height
            draw.rectangle([meter_x, height - fill_h, meter_x + meter_w, height], fill=(233, 30, 99))

            # 4. TITANIC TEXT (The Fix: Using a separate layer for massive text)
            score_txt = f"{percent}%"
            score_layer = Image.new("RGBA", (width, height), (0,0,0,0))
            score_draw = ImageDraw.Draw(score_layer)
            
            font_paths = ["arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
            font = None
            for p in font_paths:
                try:
                    font = ImageFont.truetype(p, 180)
                    break
                except: continue
            
            if not font: font = ImageFont.load_default()

            # Drawing text on the transparent layer first
            # Shadow
            score_draw.text((width//2 + 5, height//2 + 5), score_txt, fill=(0, 0, 0, 180), anchor="mm", font=font)
            # Main
            score_draw.text((width//2, height//2), score_txt, fill=(255, 255, 255, 255), anchor="mm", font=font)

            # 5. FINAL MERGE (Layered)
            canvas.paste(img1, (20, 20), mask)
            canvas.paste(img2, (width - av_size - 20, 20), mask)
            canvas = Image.alpha_composite(canvas, score_layer)

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"PIL/AIOHTTP Error: {e}")
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, u1: discord.Member, u2: discord.Member = None):
        if u2 is None: u2, u1 = u1, ctx.author
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        random.seed(f"{min(u1.id, u2.id)}{max(u1.id, u2.id)}{today}")
        pct = random.randint(0, 100)
        random.seed()

        tier = "love" if pct == 100 else "high" if pct > 75 else "sexual" if pct > 60 else "medium" if pct > 30 else "low" if pct > 10 else "sad"
        desc = random.choice(self.lexicon[tier]).format(u1=u1.display_name, u2=u2.display_name)

        async with ctx.typing():
            try:
                # Use generate_web_ui specifically
                img = await self.generate_web_ui(u1.display_avatar.url, u2.display_avatar.url, pct)
                
                embed = discord.Embed(title="❤️ Shipped off & off!", description=f"**{u1.mention} & {u2.mention}**\n*{desc}*", color=0xE91E63)
                
                if img:
                    file = discord.File(fp=img, filename="ship.png")
                    embed.set_image(url="attachment://ship.png")
                    await ctx.send(file=file, embed=embed)
                else:
                    # If image fails, don't hang! Send text-only fallback
                    await ctx.send(content=f"⚠️ Image generation failed, but here is your result:\n**Sync: {pct}%**\n{desc}", embed=embed)
            except Exception as e:
                await ctx.send(f"❌ Professional Error: {e}")

    @commands.command(name="marry")
    async def marry(self, ctx, member: discord.Member):
        if member.id == ctx.author.id: return await ctx.send("❌ You cannot marry yourself.")
        u1_data = self.get_marriage(ctx.author.id)
        u2_data = self.get_marriage(member.id)
        if (u1_data and u1_data['spouse_id']) or (u2_data and u2_data['spouse_id']):
            return await ctx.send("❌ One of you is already married!")

        view = discord.ui.View(timeout=60)
        async def accept(interaction):
            if interaction.user.id != member.id: return
            date = datetime.now().strftime("%Y-%m-%d")
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO ship_users (user_id, spouse_id, marriage_date) VALUES (?, ?, ?)", (ctx.author.id, member.id, date))
                conn.execute("INSERT OR REPLACE INTO ship_users (user_id, spouse_id, marriage_date) VALUES (?, ?, ?)", (member.id, ctx.author.id, date))
            await interaction.response.send_message(f"💖 **{ctx.author.mention} and {member.mention} are now married!**")

        btn = discord.ui.Button(label="Accept", style=discord.ButtonStyle.green)
        btn.callback = accept
        view.add_item(btn)
        await ctx.send(f"💍 {member.mention}, {ctx.author.mention} has proposed to you! Do you accept?", view=view)

    @commands.command(name="divorce")
    async def divorce(self, ctx):
        data = self.get_marriage(ctx.author.id)
        if not data or not data['spouse_id']: return await ctx.send("❌ You are not married.")
        spouse_id = data['spouse_id']
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE ship_users SET spouse_id = NULL WHERE user_id = ?", (ctx.author.id,))
            conn.execute("UPDATE ship_users SET spouse_id = NULL WHERE user_id = ?", (spouse_id,))
        await ctx.send("💔 The marriage has been dissolved.")

async def setup(bot):
    await bot.add_cog(ArenaShip(bot))
