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
        """LEGENDARY FINAL VERSION: Blurred Background + Gargantuan Typography."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    if r1.status != 200 or r2.status != 200: return None
                    img1_raw = await r1.read()
                    img2_raw = await r2.read()
                    img1 = Image.open(io.BytesIO(img1_raw)).convert("RGBA")
                    img2 = Image.open(io.BytesIO(img2_raw)).convert("RGBA")

            # --- CANVAS ENGINE ---
            width, height = 1200, 600
            # 1. PROFESSIONAL BLURRED BACKGROUND
            bg_base = Image.new("RGBA", (width, height), (20, 22, 25, 255))
            
            # Create blurred background from avatars
            back_av1 = img1.resize((600, 600)).filter(ImageFilter.GaussianBlur(40))
            back_av2 = img2.resize((600, 600)).filter(ImageFilter.GaussianBlur(40))
            bg_base.paste(back_av1, (-100, 0), back_av1)
            bg_base.paste(back_av2, (700, 0), back_av2)
            
            # Darken the background for text contrast
            dark_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 160))
            canvas = Image.alpha_composite(bg_base, dark_overlay)
            draw = ImageDraw.Draw(canvas)
            
            # 2. SIDE ACCENT
            draw.rectangle([0, 0, 15, height], fill=(233, 30, 99))

            # 3. AVATARS (Modern Squircle)
            av_size = 460
            img1_final = ImageOps.fit(img1, (av_size, av_size))
            img2_final = ImageOps.fit(img2, (av_size, av_size))
            
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, av_size, av_size], radius=100, fill=255)

            # 4. TITANIC METER (The Split)
            meter_w = 160
            meter_x = (width // 2) - (meter_w // 2)
            draw.rectangle([meter_x, 0, meter_x + meter_w, height], fill=(10, 10, 10, 200))
            
            fill_h = (percent / 100) * height
            draw.rectangle([meter_x, height - fill_h, meter_x + meter_w, height], fill=(233, 30, 99))

            # 5. TITANIC SCORE ENGINE (400pt Scale)
            score_txt = f"{percent}%"
            score_layer = Image.new("RGBA", (width, height), (0,0,0,0))
            score_draw = ImageDraw.Draw(score_layer)
            
            font_paths = ["arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
            font = None
            for p in font_paths:
                try:
                    font = ImageFont.truetype(p, 420) 
                    break
                except: continue
            if not font: font = ImageFont.load_default()

            # Layered Text Rendering (Outer Glow -> Main)
            score_draw.text((width//2, height//2), score_txt, fill=(233, 30, 99, 60), anchor="mm", font=font, stroke_width=25, stroke_fill=(233, 30, 99, 30))
            score_draw.text((width//2, height//2), score_txt, fill=(255, 255, 255, 255), anchor="mm", font=font)

            # 6. FINAL ASSEMBLY
            canvas.paste(img1_final, (50, 70), mask)
            canvas.paste(img2_final, (width - av_size - 50, 70), mask)
            canvas = Image.alpha_composite(canvas, score_layer)

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Legendary Engine Error: {e}")
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
            img = await self.generate_web_ui(u1.display_avatar.url, u2.display_avatar.url, pct)
            embed = discord.Embed(title="❤️ Shipped off & off!", description=f"**{u1.mention} & {u2.mention}**\n*{desc}*", color=0xE91E63)
            
            if img:
                file = discord.File(fp=img, filename="ship.png")
                embed.set_image(url="attachment://ship.png")
                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(content=f"⚠️ Visual Error. Result: **Sync: {pct}%**", embed=embed)

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
