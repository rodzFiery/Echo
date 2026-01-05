import discord
from discord.ext import commands
import random
import asyncio
import os
import io
import aiohttp
import json
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageOps, ImageFont, ImageFilter
import __main__

class DungeonShip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module_name = "ship"

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
            locked_emb.description = "This server does not have an active **Premium Subscription** for the **SHIP** module.\n\nType `!premium` to unlock the Love Meter and Matchmaking system!"
            if os.path.exists("fierylogo.jpg"):
                file = discord.File("fierylogo.jpg", filename="lock.png")
                locked_emb.set_thumbnail(url="attachment://lock.png")
                await ctx.send(file=file, embed=locked_emb)
            else:
                await ctx.send(embed=locked_emb)
            return False
        return True

    async def create_ship_visual(self, u1_url, u2_url, percent):
        try:
            # 1. IMPERIAL ARENA ENGINE (1200x600 for Max Embed Fit)
            # Background logic removed: Using solid deep arena base
            canvas = Image.new("RGBA", (1200, 600), (40, 0, 5, 255))
            
            draw = ImageDraw.Draw(canvas)
            
            # 2. LOVE PARTICLE GENERATOR (Heart-shaped sparkles)
            for _ in range(50):
                px, py = random.randint(0, 1200), random.randint(0, 600)
                p_size = random.randint(5, 18)
                # Drawing heart-like triangles as sparkles
                draw.polygon([(px, py), (px+p_size, py-p_size), (px+p_size*2, py)], fill=(255, 105, 180, 160))

            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())

            av_size = 380
            av1_raw = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2_raw = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            # 3. GLADIATOR AURA & PEDESTALS
            aura = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
            a_draw = ImageDraw.Draw(aura)
            aura_color = (255, 215, 0) if percent > 75 else (255, 50, 100) if percent > 40 else (120, 120, 140)
            
            # UI Pedestals (Square backgrounds for avatars)
            a_draw.rectangle([90, 100, 100+av_size+10, 110+av_size+10], fill=(0, 0, 0, 180))
            a_draw.rectangle([740, 100, 750+av_size+10, 110+av_size+10], fill=(0, 0, 0, 180))
            
            # Platform Glows
            a_draw.ellipse([70, 90, 110+av_size+30, 130+av_size+30], fill=(aura_color[0], aura_color[1], aura_color[2], 80))
            a_draw.ellipse([720, 90, 760+av_size+30, 130+av_size+30], fill=(aura_color[0], aura_color[1], aura_color[2], 80))
            aura = aura.filter(ImageFilter.GaussianBlur(35))
            canvas = Image.alpha_composite(canvas, aura)

            # Paste Avatars
            canvas.paste(av1_raw, (100, 110), av1_raw)
            canvas.paste(av2_raw, (750, 110), av2_raw)

            # 4. THE IMPERIAL BOND (Center)
            # Central Light Nova
            nova = Image.new("RGBA", (1200, 600), (0,0,0,0))
            ImageDraw.Draw(nova).ellipse([400, 100, 800, 500], fill=(255, 255, 255, 30))
            nova = nova.filter(ImageFilter.GaussianBlur(50))
            canvas = Image.alpha_composite(canvas, nova)

            # --- VERTICAL LOVE COLUMN (CENTERED) ---
            col_x, col_y, col_w, col_h = 585, 110, 30, 380
            # Column Background
            draw.rounded_rectangle([col_x, col_y, col_x + col_w, col_y + col_h], radius=15, fill=(20, 0, 0, 180), outline=(255, 255, 255, 60), width=2)
            # Love Fill (Bottom-up)
            fill_size = int((percent / 100) * (col_h - 6))
            if fill_size > 0:
                draw.rounded_rectangle([col_x + 3, col_y + col_h - 3 - fill_size, col_x + col_w - 3, col_y + col_h - 3], radius=12, fill=(255, 0, 40, 220))

            # Dynamic Percentage Color Selection
            if percent >= 90:
                text_main = (255, 69, 0)   # Fiery Red-Orange
                text_stroke = (255, 215, 0) # Gold Stroke
            elif percent >= 70:
                text_main = (255, 215, 0)  # Pure Gold
                text_stroke = (0, 0, 0)
            else:
                text_main = (220, 220, 220) # Imperial Silver
                text_stroke = (0, 0, 0)

            # Massive focal Percentage (CENTERED BETWEEN AVATARS)
            pct_text = f"{percent}%"
            # Multi-layered text for maximum visibility (VERY BIG AT THE MIDDLE)
            draw.text((608, 308), pct_text, fill=(0, 0, 0, 200), anchor="mm", size=230) # Shadow
            draw.text((600, 300), pct_text, fill=text_main, anchor="mm", size=230, stroke_width=6, stroke_fill=text_stroke)

            # Status Icon with Dynamic Glow for high scores
            heart_emoji = "❤️" if percent > 50 else "💔"
            if percent >= 75:
                heart_glow = Image.new("RGBA", (1200, 600), (0,0,0,0))
                hg_draw = ImageDraw.Draw(heart_glow)
                hg_draw.text((600, 435), heart_emoji, anchor="mm", size=110, fill=(text_main[0], text_main[1], text_main[2], 150))
                heart_glow = heart_glow.filter(ImageFilter.GaussianBlur(15))
                canvas = Image.alpha_composite(canvas, heart_glow)
            
            draw.text((600, 435), heart_emoji, anchor="mm", size=100, fill=text_main if percent >= 75 else None)

            # Fiery Logo Placement
            if os.path.exists("fierylogo.jpg"):
                logo = Image.open("fierylogo.jpg").convert("RGBA").resize((135, 135))
                mask = Image.new("L", (135, 135), 0)
                ImageDraw.Draw(mask).ellipse([0, 0, 135, 135], fill=255)
                logo.putalpha(mask)
                canvas.paste(logo, (532, 35), logo)

            # 5. DYNAMIC LOVE BAR (Imperial Shield Style)
            bar_w, bar_h = 900, 35
            bx, by = (1200-bar_w)//2, 530
            draw.rounded_rectangle([bx-8, by-8, bx+bar_w+8, by+bar_h+8], radius=15, fill=(0, 0, 0, 180)) 
            
            fill_w = (percent / 100) * bar_w
            if fill_w > 10:
                draw.rounded_rectangle([bx, by, bx+fill_w, by+bar_h], radius=10, fill=(255, 45, 95))

            # 6. FINAL CINEMATIC VIGNETTE
            vig = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
            ImageDraw.Draw(vig).rectangle([0,0,1200,600], outline=(30, 0, 5, 240), width=120)
            vig = vig.filter(ImageFilter.GaussianBlur(70))
            canvas = Image.alpha_composite(canvas, vig)

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except:
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, member: discord.Member = None):
        if member is None:
            return await ctx.send("💘 **THE ORACLE NEEDS A PARTNER!** Mention someone to challenge the fates!")
        
        if member.id == ctx.author.id:
            return await ctx.send("🎭 Narcissus? Try shipping with someone else!")

        percent = random.randint(0, 100)
        
        if percent >= 90: title = "👑 ABSOLUTE DYNASTY"
        elif percent >= 70: title = "💖 ETERNAL FLAME"
        elif percent >= 50: title = "⚖️ BALANCED DESTINY"
        elif percent >= 20: title = "☁️ FADING EMBERS"
        else: title = "💀 DOOMED ROMANCE"

        async with ctx.typing():
            ship_img = await self.create_ship_visual(ctx.author.display_avatar.url, member.display_avatar.url, percent)
            
            embed = discord.Embed(title=f"🏹 {title}", color=0xff4500)
            embed.description = f"### {ctx.author.mention} 💓 {member.mention}"
            
            if ship_img:
                file = discord.File(ship_img, filename="ship.png")
                embed.set_image(url="attachment://ship.png")
                
            embed.set_footer(text="Glory to the Echo! | Master Matchmaker", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            
            if ship_img:
                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(embed=embed)

    @commands.command(name="matchme")
    async def matchme(self, ctx):
        """Scans the arena for top 5 romantic tension candidates."""
        async with ctx.typing():
            potential_members = [m for m in ctx.guild.members if not m.bot and m.id != ctx.author.id]
            
            if len(potential_members) < 5:
                return await ctx.send("❌ Not enough gladiators in the arena to find a match!")

            sample = random.sample(potential_members, min(len(potential_members), 15))
            matches = []
            
            for m in sample:
                matches.append((m, random.randint(1, 100)))

            matches.sort(key=lambda x: x[1], reverse=True)
            top_5 = matches[:5]

            embed = discord.Embed(
                title="🔥 ARENA MATCHMAKER: POSITIVE TENSION SCAN", 
                description=f"Gladiator {ctx.author.mention}, the fates have spoken. Here are your top potential bonds:",
                color=0xFF4500
            )

            if os.path.exists("fierylogo.jpg"):
                logo_file = discord.File("fierylogo.jpg", filename="logo.png")
                embed.set_thumbnail(url="attachment://logo.png")

            results_text = ""
            for i, (member, score) in enumerate(top_5, 1):
                indicator = "👑" if score >= 90 else "🔥" if score >= 70 else "💖" if score >= 50 else "✨"
                results_text += f"**{i}. {member.display_name}** — {score}% {indicator}\n"

            embed.add_field(name="🏛️ TOP POTENTIAL MATCHES", value=results_text, inline=False)
            embed.set_footer(text="Glory to the Echo! | Try !ship with them to confirm.", icon_url=ctx.author.display_avatar.url)

            if os.path.exists("fierylogo.jpg"):
                await ctx.send(file=logo_file, embed=embed)
            else:
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DungeonShip(bot))
