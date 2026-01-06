import discord
from discord.ext import commands
import random
import io
import aiohttp
import os
import sqlite3
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import __main__

class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- IMAGE GENERATION SECTION ---
    def create_ship_card(self, avatar1_bytes, avatar2_bytes, percentage):
        width, height = 1200, 600
        canvas = Image.new('RGB', (width, height), color='#2c0003')
        draw = ImageDraw.Draw(canvas, "RGBA")
        
        # Background Gradient
        for i in range(height):
            r = int(44 + (i / height) * 60)
            draw.line([(0, i), (width, i)], fill=(r, 0, 3))

        # ADDITION: Floating Fire Particles
        for _ in range(40):
            p_x = random.randint(0, width)
            p_y = random.randint(0, height)
            p_size = random.randint(2, 6)
            draw.ellipse([p_x, p_y, p_x + p_size, p_y + p_size], fill=(255, 165, 0, 100))

        # Avatar Processing
        def process_avatar(avatar_bytes):
            img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            img = img.resize((250, 250))
            # Flame Outline Glow
            glow = Image.new("RGBA", (280, 280), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(glow)
            color = (255, 69, 0, 180) if percentage > 50 else (100, 100, 100, 150)
            g_draw.rectangle([0, 0, 280, 280], fill=color)
            glow = glow.filter(ImageFilter.GaussianBlur(15))
            return img, glow

        av1, glow1 = process_avatar(avatar1_bytes)
        av2, glow2 = process_avatar(avatar2_bytes)

        canvas.paste(glow1, (85, 160), glow1)
        canvas.paste(av1, (100, 175), av1)
        canvas.paste(glow2, (835, 160), glow2)
        canvas.paste(av2, (850, 175), av2)

        # Vertical Compatibility Column
        bar_x, bar_y, bar_w, bar_h = 540, 100, 120, 400
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(0, 0, 0, 180)) 
        
        fill_height = int((percentage / 100) * bar_h)
        fill_top_y = (bar_y + bar_h) - fill_height
        
        if fill_height > 5:
            draw.rectangle([bar_x + 10, fill_top_y, bar_x + bar_w - 10, bar_y + bar_h - 5], fill="#39FF14")

        # Text & Titles
        try:
            # Note: Ensure arial.ttf is in your project folder or use a system path
            font_pct = ImageFont.truetype("arial.ttf", 100)
            font_sub = ImageFont.truetype("arial.ttf", 40)
        except:
            font_pct = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        draw.text((600, 300), f"{percentage}%", fill="white", font=font_pct, anchor="mm", stroke_width=5, stroke_fill="black")
        draw.text((600, 50), "SHIP COMPATIBILITY", fill="#FF4500", font=font_sub, anchor="mm")

        if percentage < 25:
            draw.text((600, 540), "💔 IT'S COLD IN HERE 💔", fill="white", font=font_sub, anchor="mm")
        elif percentage > 85:
            draw.text((600, 540), "🔥🔥 TRUE LOVE 🔥🔥", fill="#FFD700", font=font_sub, anchor="mm")

        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    # --- COMMAND SECTION ---
    @commands.command(name="ship")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member = None):
        # If only one user is mentioned, ship the author with that user
        if user2 is None:
            user2 = user1
            user1 = ctx.author

        async with ctx.typing():
            percentage = random.randint(0, 100)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(user1.display_avatar.url) as resp1:
                    av1_data = await resp1.read()
                async with session.get(user2.display_avatar.url) as resp2:
                    av2_data = await resp2.read()

            # Call the internal method using self
            image_buffer = self.create_ship_card(av1_data, av2_data, percentage)
            
            file = discord.File(fp=image_buffer, filename="ship_result.png")
            embed = discord.Embed(
                title="💖 Ship Result 💖",
                description=f"**{user1.display_name}** x **{user2.display_name}**",
                color=0xff0000
            )
            embed.set_image(url="attachment://ship_result.png")
            await ctx.send(file=file, embed=embed)

# ADDITION: Setup function for Cogs
async def setup(bot):
    await bot.add_cog(Ship(bot))
