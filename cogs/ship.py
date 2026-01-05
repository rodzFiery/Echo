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
            # 1. CELESTIAL CANVAS ENGINE
            # Deep space triple-gradient background
            canvas = Image.new("RGBA", (1200, 500), (10, 5, 20, 255))
            draw = ImageDraw.Draw(canvas)
            
            # Layering a central "Nova Burst"
            nova = Image.new("RGBA", (1200, 500), (0, 0, 0, 0))
            n_draw = ImageDraw.Draw(nova)
            nova_color = (255, 50, 150, 60) if percent > 50 else (100, 100, 255, 60)
            for i in range(15):
                n_rad = 350 - (i * 20)
                n_draw.ellipse([600-n_rad, 250-n_rad, 600+n_rad, 250+n_rad], fill=(nova_color[0], nova_color[1], nova_color[2], 8))
            nova = nova.filter(ImageFilter.GaussianBlur(30))
            canvas = Image.alpha_composite(canvas, nova)

            # 2. PARTICLE GENERATOR
            # Adding star-dust particles across the field
            for _ in range(60):
                px, py = random.randint(0, 1200), random.randint(0, 500)
                p_size = random.randint(1, 3)
                draw.ellipse([px, py, px+p_size, py+p_size], fill=(255, 255, 255, random.randint(100, 255)))

            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())

            av_size = 350
            av1_raw = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2_raw = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            # 3. POWER AURA LOGIC (Behind Avatars)
            aura = Image.new("RGBA", (1200, 500), (0, 0, 0, 0))
            a_draw = ImageDraw.Draw(aura)
            aura_color = (255, 0, 100) if percent > 60 else (0, 200, 255) if percent > 30 else (150, 150, 150)
            
            # Left Aura
            a_draw.rectangle([90, 65, 100+av_size+10, 75+av_size+10], fill=(aura_color[0], aura_color[1], aura_color[2], 120))
            # Right Aura
            a_draw.rectangle([740, 65, 750+av_size+10, 75+av_size+10], fill=(aura_color[0], aura_color[1], aura_color[2], 120))
            aura = aura.filter(ImageFilter.GaussianBlur(25))
            canvas = Image.alpha_composite(canvas, aura)

            # Paste Avatars (Square/Borderless)
            canvas.paste(av1_raw, (100, 75), av1_raw)
            canvas.paste(av2_raw, (750, 75), av2_raw)

            # 4. THE BOND UI (Center)
            # Neon Connection Line
            draw.rectangle([450, 248, 750, 252], fill=(255, 255, 255, 180))
            
            # High-Visibility Percentage (Multi-Layered Text)
            pct_text = f"{percent}%"
            # Text Glow/Shadow
            draw.text((604, 254), pct_text, fill=(0, 0, 0, 180), anchor="mm", size=170)
            # Main Text
            draw.text((600, 250), pct_text, fill=(255, 255, 255), anchor="mm", size=170, stroke_width=3, stroke_fill=(0,0,0))

            # Fiery Logo Placement
            if os.path.exists("fierylogo.jpg"):
                logo = Image.open("fierylogo.jpg").convert("RGBA").resize((120, 120))
                # Circular crop for branding
                mask = Image.new("L", (120, 120), 0)
                ImageDraw.Draw(mask).ellipse([0, 0, 120, 120], fill=255)
                logo.putalpha(mask)
                canvas.paste(logo, (540, 30), logo)

            # 5. DYNAMIC LOVE BAR (Glassmorphism)
            bar_w, bar_h = 850, 20
            bx, by = (1200-bar_w)//2, 440
            # Bar Container
            draw.rounded_rectangle([bx-2, by-2, bx+bar_w+2, by+bar_h+2], radius=10, fill=(255, 255, 255, 40))
            # Bar Fill
            fill_w = (percent / 100) * bar_w
            if fill_w > 5:
                draw.rounded_rectangle([bx, by, bx+fill_w, by+bar_h], radius=10, fill=aura_color)

            # 6. VIGNETTE POLISH
            vig = Image.new("RGBA", (1200, 500), (0, 0, 0, 0))
            ImageDraw.Draw(vig).rectangle([0,0,1200,500], outline=(0,0,0,200), width=60)
            vig = vig.filter(ImageFilter.GaussianBlur(50))
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
