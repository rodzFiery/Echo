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
            canvas = Image.new("RGBA", (1200, 600), (40, 0, 5, 255))
            
            # Use fight.jpg if it exists for the Gladiator theme
            if os.path.exists("fight.jpg"):
                bg = Image.open("fight.jpg").convert("RGBA").resize((1200, 600))
                # Add a warm pink/red romantic tint to the arena
                tint = Image.new("RGBA", (1200, 600), (255, 20, 147, 40))
                bg = Image.alpha_composite(bg, tint)
                canvas.paste(bg, (0, 0))
            
            draw = ImageDraw.Draw(canvas)
            
            # 2. LOVE PARTICLE GENERATOR (Heart-shaped sparkles)
            for _ in range(40):
                px, py = random.randint(0, 1200), random.randint(0, 600)
                p_size = random.randint(5, 15)
                # Drawing tiny heart-like triangles as sparkles
                draw.polygon([(px, py), (px+p_size, py-p_size), (px+p_size*2, py)], fill=(255, 105, 180, 150))

            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())

            av_size = 380
            av1_raw = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2_raw = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            # 3. GLADIATOR AURA (Behind Avatars)
            aura = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
            a_draw = ImageDraw.Draw(aura)
            # Gold/Crimson theme for the Arena
            aura_color = (255, 215, 0) if percent > 75 else (255, 50, 100) if percent > 40 else (100, 100, 100)
            
            # Left Platform Glow
            a_draw.ellipse([80, 100, 100+av_size+20, 120+av_size+20], fill=(aura_color[0], aura_color[1], aura_color[2], 100))
            # Right Platform Glow
            a_draw.ellipse([730, 100, 750+av_size+20, 120+av_size+20], fill=(aura_color[0], aura_color[1], aura_color[2], 100))
            aura = aura.filter(ImageFilter.GaussianBlur(30))
            canvas = Image.alpha_composite(canvas, aura)

            # Paste Avatars
            canvas.paste(av1_raw, (100, 110), av1_raw)
            canvas.paste(av2_raw, (750, 110), av2_raw)

            # 4. THE IMPERIAL BOND (Center)
            # Massive High-Visibility Percentage
            pct_text = f"{percent}%"
            # Multi-layered "Gladiator Gold" Text Effect
            draw.text((606, 306), pct_text, fill=(0, 0, 0, 180), anchor="mm", size=220) # Deep shadow
            draw.text((600, 300), pct_text, fill=(255, 215, 0), anchor="mm", size=220, stroke_width=5, stroke_fill=(0,0,0))

            # Centered Heart Icon
            heart_emoji = "❤️" if percent > 50 else "💔"
            draw.text((600, 420), heart_emoji, anchor="mm", size=80)

            # Fiery Logo Placement
            if os.path.exists("fierylogo.jpg"):
                logo = Image.open("fierylogo.jpg").convert("RGBA").resize((130, 130))
                mask = Image.new("L", (130, 130), 0)
                ImageDraw.Draw(mask).ellipse([0, 0, 130, 130], fill=255)
                logo.putalpha(mask)
                canvas.paste(logo, (535, 40), logo)

            # 5. DYNAMIC LOVE BAR (Imperial Shield Style)
            bar_w, bar_h = 900, 30
            bx, by = (1200-bar_w)//2, 520
            draw.rounded_rectangle([bx-5, by-5, bx+bar_w+5, by+bar_h+5], radius=15, fill=(0, 0, 0, 150)) # Shield border
            
            fill_w = (percent / 100) * bar_w
            if fill_w > 10:
                draw.rounded_rectangle([bx, by, bx+fill_w, by+bar_h], radius=10, fill=(255, 50, 80))

            # 6. FINAL CINEMATIC VIGNETTE
            vig = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
            ImageDraw.Draw(vig).rectangle([0,0,1200,600], outline=(20, 0, 0, 220), width=100)
            vig = vig.filter(ImageFilter.GaussianBlur(60))
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

async def setup(bot):
    await bot.add_cog(DungeonShip(bot))
