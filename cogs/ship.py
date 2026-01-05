import discord
from discord.ext import commands
import random
import asyncio
import os
import io
import aiohttp
import json
import sqlite3
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageOps, ImageFont, ImageFilter
import __main__

class DungeonShip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module_name = "ship"
        self.AUDIT_CHANNEL_ID = 1438810509322223677
        self.db_path = "/app/data/ship_data.db" if os.path.exists("/app/data") else "ship_data.db"
        self._init_db()
        
        self.arena_lexicon = {
            "sad": [
                "The Arena is silent. {u1} and {u2} have no tactical synergy.",
                "Total Dissonance. Their blades clash in conflict, not in union.",
                "The Emperor turns his thumb down. This pairing is executed by silence."
            ],
            "low": [
                "Mere recruits. {u1} and {u2} barely recognize each other's combat style.",
                "A cold sparring session. No heat detected in the training pits.",
                "Functional at best. They can share a shield, but never a soul."
            ],
            "medium": [
                "The crowd begins to roar. A spark of combat passion between {u1} and {u2}.",
                "Synchronized Strikes. They move with a rhythm that suggests a deeper bond.",
                "Arena Tension. The sand heat rises when these two enter the pit together."
            ],
            "sexual": [
                "🔥 **PIT FRICTION.** The Colosseum air grows thick with primal desire.",
                "69% Sync - Tactical and carnal alignment achieved in the heat of battle.",
                "Warrior's Ecstasy. They fight for glory, but stay for the touch."
            ],
            "high": [
                "Legendary Duo. They have conquered the pits and claimed each other.",
                "Blood-Bound. {u1} and {u2} are a storm of steel and obsession.",
                "The Arena's Favorites. Their bond is the gold standard of the empire."
            ],
            "love": [
                "👑 **IMPERIAL DYNASTY.** 100% Sync. {u1} and {u2} are the gods of the Arena.",
                "Eternal Champion Bond. Two gladiators, one unbreakable soul.",
                "The Great Flame. Their union burns brighter than the Emperor's palace."
            ]
        }

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ship_users (
                    user_id INTEGER PRIMARY KEY,
                    spouse_id INTEGER,
                    marriage_date TEXT,
                    arena_points INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def get_ship_user(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute("SELECT * FROM ship_users WHERE user_id = ?", (user_id,)).fetchone()
            if not user:
                conn.execute("INSERT INTO ship_users (user_id) VALUES (?)", (user_id,))
                conn.commit()
                return {"user_id": user_id, "spouse_id": None, "marriage_date": None, "arena_points": 0}
            return dict(user)

    async def cog_check(self, ctx):
        guild_id = str(ctx.guild.id)
        is_premium = False
        if hasattr(__main__, "PREMIUM_GUILDS"):
            guild_data = __main__.PREMIUM_GUILDS.get(guild_id, {})
            expiry = guild_data.get(self.module_name)
            if expiry and float(expiry) > datetime.now(timezone.utc).timestamp():
                is_premium = True
        
        if not is_premium:
            locked_emb = discord.Embed(title="⚔️ ARENA MODULE LOCKED", color=0xFF0000)
            locked_emb.description = "This server's **Gladiator License** for the **SHIP** module is inactive.\n\nType `!premium` to unlock the Arena Bonds."
            await ctx.send(embed=locked_emb)
            return False
        return True

    async def create_ship_visual(self, u1_url, u2_url, percent):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())

            canvas = Image.new("RGBA", (1200, 700), (10, 8, 5, 255))
            draw = ImageDraw.Draw(canvas)
            av_size = 480

            av1 = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2 = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            # --- DYNAMIC NEON COLOR ---
            if percent >= 90: neon = (255, 0, 100) # Imperial Rose
            elif percent >= 70: neon = (255, 215, 0) # Gold
            elif percent >= 50: neon = (0, 255, 200) # Cyan Spark
            else: neon = (150, 150, 150) # Cold Steel

            # --- CRYSTAL CORE RADIANCE ---
            glow_layer = Image.new("RGBA", (1200, 700), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(glow_layer)
            g_draw.ellipse([400, 100, 800, 600], fill=(*neon, 50))
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(50))
            canvas.alpha_composite(glow_layer)

            # --- TITANIC FONT ENGINE ---
            # Font sizing scaled to be gargantuan
            font_size = 450 if percent == 100 else 350 if percent >= 80 else 250
            try:
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") else "arial.ttf"
                font_main = ImageFont.truetype(font_path, font_size)
            except:
                font_main = ImageFont.load_default()

            # --- THE IMPERIAL SEAL (100% ONLY) ---
            if percent == 100:
                seal = Image.new("RGBA", (1200, 700), (0,0,0,0))
                s_draw = ImageDraw.Draw(seal)
                # Crown shape polygon
                points = [(600, 100), (650, 200), (750, 200), (670, 280), (700, 380), (600, 320), (500, 380), (530, 280), (450, 200), (550, 200)]
                s_draw.polygon(points, fill=(255, 215, 0, 100), outline=(255, 255, 255, 180), width=5)
                canvas.alpha_composite(seal)

            # --- NEON SCORE PULSE ---
            score_text = f"{percent}%"
            # Outer Neon Glow (Blurred Stroke)
            for i in range(15, 0, -2):
                alpha = int(150 * (1 - i/15))
                draw.text((600, 350), score_text, fill=(0,0,0,0), anchor="mm", font=font_main, stroke_width=i, stroke_fill=(*neon, alpha))
            
            # Focal Score
            draw.text((600, 350), score_text, fill=(255, 255, 255, 255), anchor="mm", font=font_main, stroke_width=4, stroke_fill=(255,255,255))

            # --- GLADIATOR FRAMES ---
            draw.rectangle([45, 145, 45+av_size+10, 145+av_size+10], outline=neon, width=15)
            draw.rectangle([715, 145, 715+av_size+10, 145+av_size+10], outline=neon, width=15)

            canvas.paste(av1, (50, 150), av1)
            canvas.paste(av2, (720, 150), av2)

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Arena Visual Error: {e}")
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member = None):
        """⚔️ Test the bond of two Gladiators."""
        if user2 is None:
            user2, user1 = user1, ctx.author

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seed_str = f"{min(user1.id, user2.id)}{max(user1.id, user2.id)}{today}"
        random.seed(seed_str)
        percent = random.randint(0, 100)
        random.seed()

        tier = "sad" if percent < 20 else "low" if percent < 40 else "medium" if percent < 60 else "sexual" if percent < 80 else "high" if percent < 100 else "love"
        msg = random.choice(self.arena_lexicon[tier]).format(u1=user1.display_name, u2=user2.display_name)

        embed = discord.Embed(title="🏟️ ARENA BOND SYNCHRONIZATION 🏟️", color=0xdaa520)
        embed.description = f"**Gladiators:** {user1.mention} & {user2.mention}\n\n**Arena Sync: {percent}%**\n> *{msg}*"
        
        async with ctx.typing():
            img_buf = await self.create_ship_visual(user1.display_avatar.url, user2.display_avatar.url, percent)
            if img_buf:
                file = discord.File(img_buf, filename="arena_bond.png")
                embed.set_image(url="attachment://arena_bond.png")
                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(embed=embed)

    @commands.command(name="marry", aliases=["arena_bond"])
    async def marry(self, ctx, member: discord.Member):
        """💍 Seal a permanent contract in the pits."""
        if member.id == ctx.author.id: return await ctx.send("❌ A gladiator cannot bond with their own shadow.")
        u1, u2 = self.get_ship_user(ctx.author.id), self.get_ship_user(member.id)
        if u1['spouse_id'] or u2['spouse_id']: return await ctx.send("❌ One of you is already bound by an Imperial Contract.")

        view = discord.ui.View(timeout=60)
        async def accept_callback(interaction):
            if interaction.user.id != member.id: return
            date = datetime.now().strftime("%Y-%m-%d")
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE ship_users SET spouse_id = ?, marriage_date = ? WHERE user_id = ?", (member.id, date, ctx.author.id))
                conn.execute("UPDATE ship_users SET spouse_id = ?, marriage_date = ? WHERE user_id = ?", (ctx.author.id, date, member.id))
            
            res_emb = discord.Embed(title="⚔️ IMPERIAL CONTRACT SEALED", color=0x00ff00)
            res_emb.description = f"The Emperor has signed the decree. **{ctx.author.display_name}** and **{member.display_name}** are now bound forever."
            await interaction.response.send_message(embed=res_emb)

        btn = discord.ui.Button(label="Accept Bond", style=discord.ButtonStyle.success, emoji="⚔️")
        btn.callback = accept_callback
        view.add_item(btn)
        
        propose_emb = discord.Embed(title="🛡️ ARENA PROPOSAL", color=0xff4500)
        propose_emb.description = f"{member.mention}, Gladiator {ctx.author.mention} offers you a life-long contract in the pits. Do you accept?"
        await ctx.send(embed=propose_emb, view=view)

    @commands.command(name="divorce", aliases=["sever"])
    async def divorce(self, ctx):
        """💔 Sever an Imperial Contract."""
        u = self.get_ship_user(ctx.author.id)
        if not u['spouse_id']: return await ctx.send("❌ You are currently unbound.")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE ship_users SET spouse_id = NULL, marriage_date = NULL WHERE user_id = ?", (ctx.author.id,))
            conn.execute("UPDATE ship_users SET spouse_id = NULL, marriage_date = NULL WHERE user_id = ?", (u['spouse_id'],))
        
        await ctx.send("🏚️ **CONTRACT SEVERED.** The Arena reclaims your individual status.")

async def setup(bot):
    await bot.add_cog(DungeonShip(bot))
