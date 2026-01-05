import discord
from discord.ext import commands
import random
import asyncio
import os
import io
import aiohttp
import json
import sys
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageOps, ImageFont, ImageFilter
import __main__

class DungeonShip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module_name = "ship"
        self.AUDIT_CHANNEL_ID = 1438810509322223677
        
        # CATEGORIZED LEXICON
        self.erotic_lexicon = {
            "sad": [
                "A cold void. {u1} and {u2} are like oil and water in a dark cell.",
                "Repulsion. The chains between them shatter before they can even lock.",
                "Zero. Nada. The dungeon lights flicker and die at the sight of them."
            ],
            "low": [
                "Stiff and formal. A purely professional arrangement of pain.",
                "Functional compatibility. They can occupy the same dungeon, barely.",
                "A flicker of hope, immediately extinguished by reality."
            ],
            "medium": [
                "Tension is building. The Red Room feels a little smaller when they are together.",
                "The chains are beginning to hum with anticipation.",
                "The friction is consistent. A pleasant hum in the dark."
            ],
            "sexual": [
                "🔞 **PEAK FRICTION.** The dungeon air grows thick when they touch.",
                "69% - The perfect balance of oral tradition and heavy restraints.",
                "Absolute carnal dominance. Neither wants to stop."
            ],
            "high": [
                "Dangerous obsession. They are losing track of the game in each other's eyes.",
                "Soul-binding heat. The collar is locked, and they both threw away the key.",
                "They are the gold standard for compatibility in the Red Room."
            ],
            "love": [
                "💖 **ETERNAL POSSESSION.** 100% Love. {u1} has claimed {u2}'s soul forever.",
                "Two bodies, one heartbeat. The dungeon has produced a masterpiece of love.",
                "The chains have turned to gold. A perfect 100."
            ]
        }

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
            locked_emb.description = "This server does not have an active **Premium Subscription** for the **SHIP** module.\n\nType `!premium` to unlock the Love Meter!"
            if os.path.exists("fierylogo.jpg"):
                file = discord.File("fierylogo.jpg", filename="lock.png")
                locked_emb.set_thumbnail(url="attachment://lock.png")
                await ctx.send(file=file, embed=locked_emb)
            else:
                await ctx.send(embed=locked_emb)
            return False
        return True

    async def create_ship_visual(self, u1_url, u2_url, percent):
        """Generates visual match with SQUARE avatars and high-visibility central green ruler."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data = io.BytesIO(await r1.read())
                    p2_data = io.BytesIO(await r2.read())

            canvas_width, canvas_height = 1200, 700
            canvas = Image.new("RGBA", (canvas_width, canvas_height), (10, 0, 5, 255))
            draw = ImageDraw.Draw(canvas)

            # Square Avatars
            av_size = 400
            av1_img = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2_img = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            def apply_erotic_frame_square(avatar, color, pulse_intensity):
                glow_size = av_size + 80
                glow = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
                draw_g = ImageDraw.Draw(glow)
                glow_range = 20 + pulse_intensity 
                for i in range(glow_range, 0, -1):
                    alpha = int(220 * (1 - i/glow_range))
                    draw_g.rectangle([i, i, glow_size-i, glow_size-i], outline=(*color, alpha), width=5)
                glow.paste(avatar, (40, 40), avatar)
                return glow

            frame_color = (255, 20, 147) # Hot Pink
            pulse = int((percent / 100) * 10) 
            if percent == 69: frame_color = (255, 0, 255) 
            elif percent >= 90: frame_color = (255, 0, 80) 

            av1_framed = apply_erotic_frame_square(av1_img, frame_color, pulse)
            av2_framed = apply_erotic_frame_square(av2_img, frame_color, pulse)

            canvas.paste(av1_framed, (20, 150), av1_framed)
            canvas.paste(av2_framed, (canvas_width - av_size - 100, 150), av2_framed)

            # CENTRAL RULER
            col_x, col_y, col_w, col_h = (canvas_width // 2) - 60, 120, 120, 480
            draw.rectangle([col_x, col_y, col_x + col_w, col_y + col_h], fill=(20, 20, 20), outline=(255, 255, 255), width=5)
            
            fill_height = (percent / 100) * col_h
            if percent > 0:
                draw.rectangle([col_x + 8, (col_y + col_h) - fill_height, col_x + col_w - 8, col_y + col_h - 8], fill=(50, 255, 50))

            # Score Text
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                font = ImageFont.load_default()
            
            score_text = f"{percent}%"
            draw.text(((canvas_width // 2) - 60, 20), score_text, fill=(255, 255, 255), font=font, stroke_width=4, stroke_fill=(0,0,0))

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Visual Error: {e}")
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member = None):
        """LEGENDARY SHIP: Calculate synchronization between assets."""
        if user2 is None:
            user2, user1 = user1, ctx.author

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seed_str = f"{min(user1.id, user2.id)}{max(user1.id, user2.id)}{today}"
        random.seed(seed_str)
        percent = random.randint(0, 100)
        random.seed()

        if percent == 0: tier = "sad"
        elif percent < 30: tier = "low"
        elif percent < 60: tier = "medium"
        elif 60 <= percent <= 75: tier = "sexual"
        elif percent < 100: tier = "high"
        else: tier = "love"

        message_template = random.choice(self.erotic_lexicon[tier])
        result_msg = message_template.format(u1=user1.display_name, u2=user2.display_name)

        main_mod = sys.modules['__main__']
        embed = main_mod.fiery_embed("🔞 SOUL SYNCHRONIZATION 🔞", f"**Assets Involved:** {user1.mention} & {user2.mention}")
        
        if percent == 69:
            embed.title = "🫦 EXHIBITIONIST PEAK REACHED 🫦"
            await main_mod.update_user_stats_async(user1.id, amount=2500, source="Ship 69% Bonus")
            await main_mod.update_user_stats_async(user2.id, amount=2500, source="Ship 69% Bonus")
            result_msg += "\n\n💰 **EXHIBITION REWARD:** +2,500 Flames added!"

        embed.add_field(name=f"📊 Compatibility: {percent}%", value=f"*{result_msg}*", inline=False)
        
        async with ctx.typing():
            img_buf = await self.create_ship_visual(user1.display_avatar.url, user2.display_avatar.url, percent)
            if img_buf:
                file = discord.File(img_buf, filename="ship.png")
                embed.set_image(url="attachment://ship.png")
                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(embed=embed)

        # AUDIT LOGGING
        if percent in [0, 69, 100]:
            audit_channel = self.bot.get_channel(self.AUDIT_CHANNEL_ID)
            if audit_channel:
                log_embed = main_mod.fiery_embed("🕵️ VOYEUR AUDIT REPORT", f"Sync detected: **{percent}%**")
                log_embed.add_field(name="Assets", value=f"{user1.mention} x {user2.mention}")
                await audit_channel.send(embed=log_embed)

    @commands.command(name="matchmaking")
    async def matchmaking(self, ctx):
        """Scans the dungeon for the highest compatibility pairs."""
        main_mod = sys.modules['__main__']
        await ctx.send("👁️ **The Master's Voyeurs are scanning for erotic frequencies...**")
        members = [m for m in ctx.channel.members if not m.bot][:40]
        if len(members) < 2: return await ctx.send("❌ Not enough assets to scan.")

        matches = []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                u1, u2 = members[i], members[j]
                seed_str = f"{min(u1.id, u2.id)}{max(u1.id, u2.id)}{today}"
                random.seed(seed_str)
                pct = random.randint(0, 100)
                random.seed()
                matches.append((u1, u2, pct))

        top_matches = sorted(matches, key=lambda x: x[2], reverse=True)[:5]
        desc = "\n".join([f"**{idx+1}.** {m1.mention} + {m2.mention} — **{pct}%**" for idx, (m1, m2, pct) in enumerate(top_matches)])
        embed = main_mod.fiery_embed("🫦 THE MASTER'S MATCHMAKING 🫦", desc)
        await ctx.send(embed=embed)

    @commands.command(name="marry")
    async def marry(self, ctx, member: discord.Member):
        """Propose a lifelong contract of submission."""
        main_mod = sys.modules['__main__']
        if member.id == ctx.author.id: return await ctx.send("❌ Cannot bind to yourself.")
        
        u1, u2 = main_mod.get_user(ctx.author.id), main_mod.get_user(member.id)
        if u1['spouse'] or u2['spouse']: return await ctx.send("❌ Contract already exists.")
        
        emb = main_mod.fiery_embed("🔞 SACRED CONTRACT OFFERED", f"{ctx.author.mention} proposes to {member.mention}.", color=0xFF1493)
        view = discord.ui.View(timeout=60)
        
        async def accept(interaction):
            if interaction.user.id != member.id: return
            today = datetime.now().strftime("%Y-%m-%d")
            with main_mod.get_db_connection() as conn:
                conn.execute("UPDATE users SET spouse = ?, marriage_date = ? WHERE id = ?", (member.id, today, ctx.author.id))
                conn.execute("UPDATE users SET spouse = ?, marriage_date = ? WHERE id = ?", (ctx.author.id, today, member.id))
            await interaction.response.send_message(f"💖 **CONTRACT SEALED.** {ctx.author.mention} and {member.mention} are bound.")
            view.stop()

        btn = discord.ui.Button(label="Accept Possession", style=discord.ButtonStyle.success, emoji="🫦")
        btn.callback = accept
        view.add_item(btn)
        await ctx.send(embed=emb, view=view)

async def setup(bot):
    await bot.add_cog(DungeonShip(bot))
    print("✅ LOG: Dungeon Ship adapt ONLINE.")
