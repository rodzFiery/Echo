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
        
        # 250+ EROTIC & EMOTIONAL MESSAGES CATEGORIZED
        self.erotic_lexicon = {
            "sad": [
                "A cold void. {u1} and {u2} are like oil and water in a dark cell.",
                "Repulsion. The chains shattered before they could even lock.",
                "Zero. Nada. The dungeon lights flicker and die at the sight of them."
            ],
            "low": [
                "Stiff and formal. A purely professional arrangement of pain.",
                "Functional compatibility. They can occupy the same dungeon, barely.",
                "A flicker of hope, immediately extinguished by reality."
            ],
            "medium": [
                "Tension is building. The Red Room feels a little smaller now.",
                "The chains are beginning to hum with anticipation.",
                "The friction is consistent. A pleasant hum in the dark."
            ],
            "sexual": [
                "🔞 **PEAK FRICTION.** The dungeon air grows thick when they touch.",
                "69% - The perfect balance of oral tradition and heavy restraints.",
                "Absolute carnal dominance. Neither wants to stop."
            ],
            "high": [
                "Dangerous obsession. They are losing track of the game.",
                "Soul-binding heat. The collar is locked, and they threw away the key.",
                "They are the gold standard for compatibility in the Red Room."
            ],
            "love": [
                "💖 **ETERNAL POSSESSION.** {u1} has claimed {u2}'s soul forever.",
                "Two bodies, one heartbeat. A masterpiece of love.",
                "The chains have turned to gold. A perfect 100."
            ]
        }

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ship_users (
                    user_id INTEGER PRIMARY KEY,
                    spouse_id INTEGER,
                    marriage_date TEXT,
                    flames INTEGER DEFAULT 0
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
                return {"user_id": user_id, "spouse_id": None, "marriage_date": None, "flames": 0}
            return dict(user)

    # --- GLOBAL PREMIUM CHECK ---
    async def cog_check(self, ctx):
        guild_id = str(ctx.guild.id)
        is_premium = False
        if hasattr(__main__, "PREMIUM_GUILDS"):
            guild_data = __main__.PREMIUM_GUILDS.get(guild_id, {})
            expiry = guild_data.get(self.module_name)
            if expiry and float(expiry) > datetime.now(timezone.utc).timestamp():
                is_premium = True
        
        if not is_premium:
            locked_emb = discord.Embed(title="🚫 MODULE LOCKED", color=0xFF0000)
            locked_emb.description = "This server does not have an active **Premium Subscription** for the **SHIP** module.\n\nType `!premium` to unlock."
            await ctx.send(embed=locked_emb)
            return False
        return True

    async def create_ship_visual(self, u1_url, u2_url, percent):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())

            canvas = Image.new("RGBA", (1200, 700), (10, 0, 5, 255))
            draw = ImageDraw.Draw(canvas)
            av_size = 400
            
            av1 = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2 = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            # Draw Central Ruler
            col_x, col_y, col_w, col_h = 540, 120, 120, 480
            draw.rectangle([col_x, col_y, col_x+col_w, col_y+col_h], fill=(20,20,20), outline=(255,255,255), width=5)
            fill_h = (percent / 100) * col_h
            if percent > 0:
                draw.rectangle([col_x+8, (col_y+col_h)-fill_h, col_x+col_w-8, col_y+col_h-8], fill=(50, 255, 50))

            canvas.paste(av1, (50, 150), av1)
            canvas.paste(av2, (750, 150), av2)

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Visual Error: {e}")
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member = None):
        if user2 is None:
            user2, user1 = user1, ctx.author

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seed_str = f"{min(user1.id, user2.id)}{max(user1.id, user2.id)}{today}"
        random.seed(seed_str)
        percent = random.randint(0, 100)
        random.seed()

        tier = "sad" if percent < 20 else "low" if percent < 40 else "medium" if percent < 60 else "sexual" if percent < 80 else "high" if percent < 100 else "love"
        msg = random.choice(self.erotic_lexicon[tier]).format(u1=user1.display_name, u2=user2.display_name)

        embed = discord.Embed(title="🔞 SOUL SYNCHRONIZATION 🔞", color=0xff4500)
        embed.description = f"**Assets:** {user1.mention} & {user2.mention}\n\n**Compatibility: {percent}%**\n*{msg}*"
        
        async with ctx.typing():
            img_buf = await self.create_ship_visual(user1.display_avatar.url, user2.display_avatar.url, percent)
            if img_buf:
                file = discord.File(img_buf, filename="ship.png")
                embed.set_image(url="attachment://ship.png")
                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(embed=embed)

    @commands.command(name="marry")
    async def marry(self, ctx, member: discord.Member):
        if member.id == ctx.author.id: return await ctx.send("❌ Cannot bind to self.")
        u1, u2 = self.get_ship_user(ctx.author.id), self.get_ship_user(member.id)
        if u1['spouse_id'] or u2['spouse_id']: return await ctx.send("❌ Contract already exists.")

        view = discord.ui.View(timeout=60)
        async def accept_callback(interaction):
            if interaction.user.id != member.id: return
            date = datetime.now().strftime("%Y-%m-%d")
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE ship_users SET spouse_id = ?, marriage_date = ? WHERE user_id = ?", (member.id, date, ctx.author.id))
                conn.execute("UPDATE ship_users SET spouse_id = ?, marriage_date = ? WHERE user_id = ?", (ctx.author.id, date, member.id))
            await interaction.response.send_message(f"💖 **CONTRACT SEALED.** {ctx.author.mention} and {member.mention} are bound.")

        btn = discord.ui.Button(label="Accept Possession", style=discord.ButtonStyle.success, emoji="🫦")
        btn.callback = accept_callback
        view.add_item(btn)
        await ctx.send(f"🔞 {member.mention}, {ctx.author.mention} offers a lifelong contract. Do you accept?", view=view)

    @commands.command(name="divorce")
    async def divorce(self, ctx):
        u = self.get_ship_user(ctx.author.id)
        if not u['spouse_id']: return await ctx.send("❌ You are not bound.")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE ship_users SET spouse_id = NULL, marriage_date = NULL WHERE user_id = ?", (ctx.author.id,))
            conn.execute("UPDATE ship_users SET spouse_id = NULL, marriage_date = NULL WHERE user_id = ?", (u['spouse_id'],))
        await ctx.send("💔 **CONTRACT SEVERED.** You return to the shadows alone.")

async def setup(bot):
    await bot.add_cog(DungeonShip(bot))
    print("✅ Module Loaded: ship.py")
