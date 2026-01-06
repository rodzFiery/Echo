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

    def create_ship_card(self, avatar1_bytes, avatar2_bytes, percentage):
        width, height = 1200, 600
        canvas = Image.new('RGB', (width, height), color='#2c0003')
        draw = ImageDraw.Draw(canvas, "RGBA")
        
        # 1. ENHANCED: Background Love Arena Gradient
        for i in range(height):
            r = int(40 + (i / height) * 90)
            g = int(0 + (i / height) * 20)
            draw.line([(0, i), (width, i)], fill=(r, g, 10))

        # ADDITION: Center Spotlight Glow (Arena Effect)
        spotlight = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(spotlight)
        for r in range(1, 500, 5):
            alpha = int(100 * (1 - r / 500))
            s_draw.ellipse([600-r, 300-r, 600+r, 300+r], outline=(255, 50, 50, alpha))
        canvas.paste(spotlight, (0, 0), spotlight)

        # 2. ENHANCED: High-Intensity Fire Particles (Embers)
        for _ in range(80): 
            p_x = random.randint(0, width)
            p_y = random.randint(0, height)
            p_size = random.randint(2, 8)
            p_color = random.choice([(255, 200, 0, 160), (255, 80, 0, 180), (255, 255, 255, 120)])
            draw.ellipse([p_x, p_y, p_x + p_size, p_y + p_size], fill=p_color)

        # 3. Avatar Processing - ZOOMED & NO BORDERS (380x380)
        def process_avatar(avatar_bytes):
            img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            img = img.resize((380, 380)) # Zoomed in further
            # ENHANCED: Circular Glow (Flame Aura) - No rectangle borders
            glow = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(glow)
            glow_color = (255, 69, 0, 220) if percentage > 50 else (180, 0, 255, 160)
            # Use ellipse instead of rectangle to remove borders
            g_draw.ellipse([0, 0, 450, 450], fill=glow_color)
            glow = glow.filter(ImageFilter.GaussianBlur(35))
            return img, glow

        av1, glow1 = process_avatar(avatar1_bytes)
        av2, glow2 = process_avatar(avatar2_bytes)

        # Adjusted positions for the ultra-zoom feel
        canvas.paste(glow1, (-35, 75), glow1)
        canvas.paste(av1, (0, 110), av1)
        canvas.paste(glow2, (785, 75), glow2)
        canvas.paste(av2, (820, 110), av2)

        # 4. ENHANCED: Bigger Glass-Morphism Compatibility Column
        # Width 180 for more impact, zoomed height
        bar_x, bar_y, bar_w, bar_h = 510, 60, 180, 480
        
        # Column Border/Frame
        draw.rectangle([bar_x-5, bar_y-5, bar_x+bar_w+5, bar_y+bar_h+5], outline=(255, 255, 255, 90), width=3)
        # Deep translucent backing
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(0, 0, 0, 230)) 
        
        fill_height = int((percentage / 100) * bar_h)
        fill_top_y = (bar_y + bar_h) - fill_height
        
        if fill_height > 5:
            # ADDITION: Gradient Fill for the Bar (Electric Green)
            for i in range(fill_top_y, bar_y + bar_h):
                intensity = int(150 + (i - fill_top_y) / (fill_height + 1) * 105)
                draw.line([(bar_x + 15, i), (bar_x + bar_w - 15, i)], fill=(57, intensity, 20, 255))

        # 5. MEGA ZOOMED PERCENTAGE LOGIC
        text_str = f"{percentage}%"
        text_canvas = Image.new('RGBA', (1000, 550), (0, 0, 0, 0))
        t_draw = ImageDraw.Draw(text_canvas)
        
        # Increased font size to 380 for the Ultra-Zoom effect
        f_size = 380 
        try:
            font_pct = ImageFont.truetype("arial.ttf", f_size)
        except:
            try:
                font_pct = ImageFont.truetype("DejaVuSans-Bold.ttf", f_size)
            except:
                font_pct = ImageFont.load_default()

        # ENHANCED: Add a neon shadow to the text layer
        t_draw.text((508, 278), text_str, fill=(255, 0, 0, 130), font=font_pct, anchor="mm")
        t_draw.text((500, 270), text_str, fill="white", font=font_pct, anchor="mm", stroke_width=16, stroke_fill="black")
        
        if font_pct.getbbox(text_str)[2] < 100: 
            text_canvas = text_canvas.resize((3000, 1600), Image.Resampling.NEAREST)
            canvas.paste(text_canvas, (-900, -500), text_canvas) 
        else:
            # Centered over the widened column
            canvas.paste(text_canvas, (100, 50), text_canvas)

        # 6. ADDITION: 100% Special Heart Icon
        if percentage == 100:
            heart_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            h_draw = ImageDraw.Draw(heart_layer)
            h_draw.text((600, 310), "💎❤️💎", fill="white", font=font_pct, anchor="mm")
            canvas.paste(heart_layer, (0, 0), heart_layer)

        # Final labels with Fiery Color
        try:
            font_sub = ImageFont.truetype("arial.ttf", 60)
            draw.text((600, 40), "❤️ LOVE ARENA ❤️", fill="#FFCC00", font=font_sub, anchor="mm", stroke_width=5, stroke_fill="black")
        except:
            draw.text((600, 40), "LOVE ARENA", fill="#FFCC00", anchor="mm")

        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @commands.command(name="ship")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member = None):
        if user2 is None:
            user2 = user1
            user1 = ctx.author

        async with ctx.typing():
            try:
                percentage = random.randint(0, 100)
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(user1.display_avatar.url)) as resp1:
                        if resp1.status != 200: raise Exception("Failed to get User1 Avatar")
                        av1_data = await resp1.read()
                    async with session.get(str(user2.display_avatar.url)) as resp2:
                        if resp2.status != 200: raise Exception("Failed to get User2 Avatar")
                        av2_data = await resp2.read()

                image_buffer = self.create_ship_card(av1_data, av2_data, percentage)
                
                file = discord.File(fp=image_buffer, filename="ship_result.png")
                embed = discord.Embed(title="⚔️ The Ship Arena Result ⚔️", color=0xff0000)
                embed.set_image(url="attachment://ship_result.png")
                
                await ctx.send(file=file, embed=embed)
                
            except Exception as e:
                print(f"Error in Ship Command: {e}")
                await ctx.send("⚠️ An error occurred while generating the ship card. Check the console.")

async def setup(bot):
    await bot.add_cog(Ship(bot))
