import discord
from discord.ext import commands
import random
import asyncio
import os
import io
import aiohttp
import json
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageOps
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
            # Create a pink/red romantic canvas
            canvas = Image.new("RGBA", (1000, 450), (60, 0, 10, 255))
            draw = ImageDraw.Draw(canvas)

            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())

            av_size = 300
            # Open and resize avatars - NO BORDERS per request
            av1 = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2 = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            # Paste Avatars
            canvas.paste(av1, (80, 75), av1)
            canvas.paste(av2, (620, 75), av2)

            # Draw Heart or Symbol in middle
            middle_x, middle_y = 500, 225
            heart_color = (255, 50, 50) if percent > 50 else (150, 150, 150)
            
            # Simple Heart shape logic
            draw.ellipse([400, 150, 600, 300], fill=heart_color)
            
            # Text for Percentage - Large and Visible
            pct_text = f"{percent}%"
            draw.text((500, 225), pct_text, fill=(255, 255, 255), anchor="mm", size=80, stroke_width=4, stroke_fill=(0,0,0))

            # Add Logo if exists
            if os.path.exists("fierylogo.jpg"):
                logo = Image.open("fierylogo.jpg").convert("RGBA").resize((100, 100))
                canvas.paste(logo, (450, 20), logo)

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except:
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, member: discord.Member = None):
        if member is None:
            return await ctx.send("💘 **THE ORACLE NEEDS A PARTNER!** Mention someone to ship with!")
        
        if member.id == ctx.author.id:
            return await ctx.send("🎭 Self-love is important, but pick someone else!")

        percent = random.randint(0, 100)
        
        # Determine Comment
        if percent > 85: comment = "💍 **A MATCH MADE IN THE HEAVENS!**"
        elif percent > 65: comment = "❤️ **Strong connection detected!**"
        elif percent > 40: comment = "⚖️ **There is potential here.**"
        elif percent > 15: comment = "☁️ **Maybe just friends?**"
        else: comment = "💀 **ABSOLUTE CATASTROPHE.**"

        async with ctx.typing():
            ship_img = await self.create_ship_visual(ctx.author.display_avatar.url, member.display_avatar.url, percent)
            
            embed = discord.Embed(title="💖 IMPERIAL MATCHMAKER", color=0xFF69B4)
            embed.description = f"### {ctx.author.mention} x {member.mention}\n{comment}"
            
            if ship_img:
                file = discord.File(ship_img, filename="ship.png")
                embed.set_image(url="attachment://ship.png")
                
            embed.set_footer(text="Glory to the Echo! | Romantic Readings Updated")
            
            if ship_img:
                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DungeonShip(bot))
