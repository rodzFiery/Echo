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
            # 1. GENERATE CINEMATIC BACKGROUND
            # We create a large 1200x500 canvas with a deep midnight-to-crimson gradient
            base = Image.new("RGBA", (1200, 500), (15, 0, 5, 255))
            overlay = Image.new("RGBA", (1200, 500), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            
            # Create a "Nebula" glow in the center
            glow_color = (255, 20, 147, 40) if percent > 50 else (100, 100, 120, 40)
            for i in range(10): # Layered radial glow
                radius = 300 + (i * 20)
                draw_ov.ellipse([600-radius, 250-radius, 600+radius, 250+radius], fill=(glow_color[0], glow_color[1], glow_color[2], 10))
            
            canvas = Image.alpha_composite(base, overlay)
            draw = ImageDraw.Draw(canvas)

            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())

            av_size = 360
            # Square avatars - 100% Borderless per request
            av1_raw = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2_raw = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            # 2. AVATAR FX: Add a subtle outer drop shadow/glow to avatars
            shadow = Image.new("RGBA", (1200, 500), (0, 0, 0, 0))
            sh_draw = ImageDraw.Draw(shadow)
            sh_draw.rectangle([95, 70, 100+av_size+5, 75+av_size+5], fill=(0,0,0,150))
            sh_draw.rectangle([745, 70, 750+av_size+5, 75+av_size+5], fill=(0,0,0,150))
            shadow = shadow.filter(ImageFilter.GaussianBlur(15))
            canvas = Image.alpha_composite(canvas, shadow)

            # Paste main avatars
            canvas.paste(av1_raw, (100, 75), av1_raw)
            canvas.paste(av2_raw, (750, 75), av2_raw)

            # 3. CENTRAL UI: THE SOUL METER
            # Frosted Glass Path
            draw.rectangle([460, 248, 740, 252], fill=(255, 255, 255, 100)) # Thin white line
            
            # Percentage with 3D shadow effect
            pct_text = f"{percent}%"
            # Draw shadow
            draw.text((603, 253), pct_text, fill=(0, 0, 0, 200), anchor="mm", size=160)
            # Draw main text
            main_text_color = (255, 255, 255) if percent > 15 else (200, 200, 200)
            draw.text((600, 250), pct_text, fill=main_text_color, anchor="mm", size=160, stroke_width=2, stroke_fill=(0,0,0))

            # 4. LOGO BRANDING
            if os.path.exists("fierylogo.jpg"):
                logo = Image.open("fierylogo.jpg").convert("RGBA").resize((130, 130))
                # Circular crop for logo to look premium
                l_mask = Image.new("L", (130, 130), 0)
                ImageDraw.Draw(l_mask).ellipse([0,0,130,130], fill=255)
                logo.putalpha(l_mask)
                canvas.paste(logo, (535, 25), logo)

            # 5. PREMIUM PROGRESS BAR
            bar_width = 900
            bar_start = (1200 - bar_width) // 2
            # Background bar (Glass effect)
            draw.rounded_rectangle([bar_start, 450, bar_start + bar_width, 465], radius=8, fill=(255, 255, 255, 30))
            
            # Filled bar (Animated color)
            bar_color = (255, 40, 100) if percent > 50 else (120, 120, 140)
            current_bar = (percent / 100) * bar_width
            if current_bar > 5: # Only draw if there is a percentage
                draw.rounded_rectangle([bar_start, 450, bar_start + current_bar, 465], radius=8, fill=bar_color)
            
            # 6. FINAL POLISH: Vignette Effect
            vignette = Image.new("RGBA", (1200, 500), (0, 0, 0, 0))
            v_draw = ImageDraw.Draw(vignette)
            v_draw.rectangle([0, 0, 1200, 500], outline=(0,0,0,180), width=80)
            vignette = vignette.filter(ImageFilter.GaussianBlur(60))
            canvas = Image.alpha_composite(canvas, vignette)

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
        
        # Unique Romantic Titles
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
