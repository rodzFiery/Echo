import discord
from discord.ext import commands
import random
import asyncio
import os
import io
import aiohttp
import json
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageOps, ImageFont
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
            # Create a professional wide canvas
            canvas = Image.new("RGBA", (1200, 500), (30, 0, 5, 255))
            draw = ImageDraw.Draw(canvas)

            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())

            av_size = 350
            # Square avatars - No Borders
            av1 = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2 = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            # Center positioning
            canvas.paste(av1, (100, 75), av1)
            canvas.paste(av2, (750, 75), av2)

            # Central UI Elements
            # Large Percentage Text
            pct_text = f"{percent}%"
            # Drawing a decorative heart backing
            heart_color = (255, 40, 100, 255) if percent > 50 else (100, 100, 100, 255)
            
            # Draw a stylized "VS" style connection bar
            draw.rectangle([450, 240, 750, 260], fill=(255, 255, 255, 50))
            
            # Main Percentage Render
            draw.text((600, 250), pct_text, fill=(255, 255, 255), anchor="mm", size=150, stroke_width=6, stroke_fill=(0,0,0))

            # Add the Fiery Logo as a watermark/stamp in the top center
            if os.path.exists("fierylogo.jpg"):
                logo = Image.open("fierylogo.jpg").convert("RGBA").resize((120, 120))
                canvas.paste(logo, (540, 30), logo)

            # Draw a progress bar at the bottom for extra visual flair
            bar_width = 800
            bar_start = (1200 - bar_width) // 2
            draw.rounded_rectangle([bar_start, 430, bar_start + bar_width, 450], radius=10, fill=(50, 50, 50))
            current_bar = (percent / 100) * bar_width
            draw.rounded_rectangle([bar_start, 430, bar_start + current_bar, 450], radius=10, fill=(255, 50, 80))

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
