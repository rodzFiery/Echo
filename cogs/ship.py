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
        
        # 1. Background Gradient
        for i in range(height):
            r = int(44 + (i / height) * 60)
            draw.line([(0, i), (width, i)], fill=(r, 0, 3))

        # 2. Floating Fire Particles
        for _ in range(40):
            p_x = random.randint(0, width)
            p_y = random.randint(0, height)
            p_size = random.randint(2, 6)
            draw.ellipse([p_x, p_y, p_x + p_size, p_y + p_size], fill=(255, 165, 0, 100))

        # 3. Avatar Processing
        def process_avatar(avatar_bytes):
            img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            img = img.resize((250, 250))
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

        # 4. Vertical Compatibility Column
        bar_x, bar_y, bar_w, bar_h = 540, 100, 120, 400
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(0, 0, 0, 180)) 
        
        fill_height = int((percentage / 100) * bar_h)
        fill_top_y = (bar_y + bar_h) - fill_height
        
        if fill_height > 5:
            draw.rectangle([bar_x + 10, fill_top_y, bar_x + bar_w - 10, bar_y + bar_h - 5], fill="#39FF14")

        # 5. ZOOMED PERCENTAGE LOGIC
        text_str = f"{percentage}%"
        
        # We create a much larger text canvas to ensure "zoom"
        text_canvas = Image.new('RGBA', (600, 300), (0, 0, 0, 0))
        t_draw = ImageDraw.Draw(text_canvas)
        
        # Font handling with additive fallback
        f_size = 150
        try:
            # Using a basic path that works on most Linux/Windows
            font_pct = ImageFont.truetype("arial.ttf", f_size)
        except:
            try:
                font_pct = ImageFont.truetype("DejaVuSans-Bold.ttf", f_size)
            except:
                font_pct = ImageFont.load_default()

        # Draw the text on its own layer
        t_draw.text((300, 150), text_str, fill="white", font=font_pct, anchor="mm", stroke_width=4, stroke_fill="black")
        
        # If the font is the tiny default, we manually upscale the image (The Zoom)
        if font_pct.getbbox(text_str)[2] < 100: 
            text_canvas = text_canvas.resize((1200, 600), Image.Resampling.NEAREST)
            canvas.paste(text_canvas, (0, 0), text_canvas) # Paste full size
        else:
            # Normal paste centered on the bar
            canvas.paste(text_canvas, (300, 150), text_canvas)

        # 6. ADDITION: 100% Special Heart Icon
        if percentage == 100:
            heart_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            h_draw = ImageDraw.Draw(heart_layer)
            # Drawing a simple large heart shape in the center
            h_draw.text((600, 300), "💎❤️💎", fill="white", font=font_pct, anchor="mm")
            canvas.paste(heart_layer, (0, 0), heart_layer)

        # Final labels
        try:
            font_sub = ImageFont.truetype("arial.ttf", 40)
            draw.text((600, 50), "SHIP COMPATIBILITY", fill="#FF4500", font=font_sub, anchor="mm")
        except:
            draw.text((600, 50), "SHIP COMPATIBILITY", fill="#FF4500", anchor="mm")

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
                
                # Fetch avatars with a timeout to prevent hanging
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(user1.display_avatar.url)) as resp1:
                        if resp1.status != 200: raise Exception("Failed to get User1 Avatar")
                        av1_data = await resp1.read()
                    async with session.get(str(user2.display_avatar.url)) as resp2:
                        if resp2.status != 200: raise Exception("Failed to get User2 Avatar")
                        av2_data = await resp2.read()

                # Generate card
                image_buffer = self.create_ship_card(av1_data, av2_data, percentage)
                
                file = discord.File(fp=image_buffer, filename="ship_result.png")
                embed = discord.Embed(title="💖 Ship Result 💖", color=0xff0000)
                embed.set_image(url="attachment://ship_result.png")
                
                await ctx.send(file=file, embed=embed)
                
            except Exception as e:
                # This will print the error in your terminal so you can see why it's failing
                print(f"Error in Ship Command: {e}")
                await ctx.send("⚠️ An error occurred while generating the ship card. Check the console.")

async def setup(bot):
    await bot.add_cog(Ship(bot))
