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
        # 140 Arena Messages Tiered by Percentage (Expanded)
        self.arena_messages = {
            "0-15": [
                "The arena is freezing over. Total mismatch.", "Ice cold. Not even a spark found.", "Security is escorting you both to different exits.", "The audience is booing. This is a disaster.", "Error 404: Love not found in this arena.", 
                "A black hole has more attraction than this.", "The tension is negative. Please stop.", "Even the embers died looking at you two.", "Zero chemistry detected. Move along.", "This isn't a ship, it's a shipwreck.", 
                "You two are on different planets.", "The arena lights just flickered and died.", "Total silence from the crowd. Awkward.", "A match made in... well, not here.", "Better luck in the next life.",
                "The Arena announcer is speechless at how bad this is.", "A cactus has a softer touch than this pairing.", "The simulation crashed trying to find compatibility.", "The fire department left because there is zero heat.", "Total system rejection."
            ],
            "16-30": [
                "Slight friction, but mostly just sparks of annoyance.", "The arena remains mostly dark.", "Maybe try talking? Or maybe don't.", "A very weak connection detected.", "The crowd is checking their phones.", 
                "Not exactly a power couple.", "Room for improvement... a lot of it.", "The love meter barely moved.", "A flicker in the dark, then nothing.", "You're both better off as solo fighters.", 
                "The arena floor is still cold.", "Minimal compatibility found.", "Are you even trying?", "The fire is struggling to start.", "A distant 'maybe' at best.",
                "The Arena janitor is more excited than you two.", "Static on the line. Too much interference.", "The spotlight is trying to find you, but it's bored.", "Like oil and water in a blender.", "A flicker of hope, but mostly just smoke."
            ],
            "31-45": [
                "The embers are starting to glow.", "A casual alliance, nothing more.", "The arena is lukewarm.", "Friends with arena benefits?", "Not a total loss, but not a win.", 
                "The crowd is curious, but not convinced.", "A steady beat, but no rhythm yet.", "You won't kill each other... probably.", "Just enough to keep the lights on.", "The arena is waiting for more.", 
                "A mild interest detected.", "Stable, but boring.", "The ship is floating, but not moving.", "Testing the waters of the arena.", "A low-level bond.",
                "The Arena spectators are leaning in slightly.", "A spark exists, but needs a lot of oxygen.", "Walking the line between friends and fighters.", "The foundation is there, but the house is empty.", "Lukewarm tea levels of passion."
            ],
            "46-60": [
                "The arena is heating up!", "A solid match for the mid-tier.", "The crowd is starting to cheer.", "Balanced power levels.", "The sparks are consistent now.", 
                "A dangerous dance in the arena.", "The tension is palpable.", "Halfway to destiny.", "The fire is growing steady.", "You look good together under the lights.", 
                "A promising future in the arena.", "The chemistry is becoming visible.", "Keep this energy going.", "A match worth watching.", "The arena floor is warming up.",
                "The crowd is starting to place bets on you two.", "Synchronized combatants in the game of love.", "A powerful rhythm is taking over the Arena.", "You're making the front row sweat.", "The heat is finally real."
            ],
            "61-75": [
                "Intense energy flowing through the arena!", "The crowd is on their feet!", "A high-tier pairing detected.", "The sparks are flying everywhere.", "The arena is glowing bright pink.", 
                "A passionate duel of hearts.", "Almost at the peak of the arena.", "The love tension is rising fast.", "The embers are turning into flames.", "A powerful connection is forming.", 
                "The stadium is roaring for you two.", "Strongest match of the hour!", "The arena lights are pulsing.", "Destined for something great.", "True arena synergy.",
                "The Arena screens are flashing 'WARNING: HIGH HEAT'.", "Your souls are resonant at a high frequency.", "The ground is literally shaking now.", "A beautiful storm is brewing in the center.", "Pure, unadulterated Arena magnetism."
            ],
            "76-90": [
                "The arena is on fire!", "A legendary pairing has entered.", "The love tension is reaching critical levels!", "Breathtaking compatibility.", "The crowd is screaming your names!", 
                "Electric. Passionate. Unstoppable.", "A high-voltage arena match.", "The heat is nearly unbearable!", "Almost perfect. Simply beautiful.", "The stadium is shaking from the tension.", 
                "A match for the ages.", "Burning brighter than the sun.", "The arena has never seen this before.", "Soulmate territory found.", "Pure arena magic.",
                "The Arena ceiling is about to blow off!", "Gravity is failing because of your attraction.", "A masterclass in romantic chemistry.", "The embers have become a localized sun.", "Elite tier compatibility achieved."
            ],
            "91-100": [
                "THE ARENA HAS EXPLODED! TRUE LOVE!", "A DIVINE MATCH MADE IN THE HEAVENS!", "ULTIMATE COMPATIBILITY DETECTED!", "THE LOVE ARENA IS IN TOTAL SHOCK!", "A PERFECT HARMONY OF SOULS!", 
                "BEYOND LEGENDARY. BEYOND PERFECTION.", "THE DESTINY METER JUST BROKE!", "UNSTOPPABLE ARENA POWER!", "THE CROWD IS WEEPING FROM JOY!", "A MATCH THAT WILL BE REMEMBERED FOREVER!", 
                "TOTAL ARENA DOMINATION BY LOVE!", "THE EMBERS HAVE TURNED INTO A SUPERNOVA!", "YOU ARE THE KINGS OF THE LOVE ARENA!", "A DIAMOND IN THE ROUGH? NO, A DIAMOND HEART!", "ABSOLUTE PERFECTION FOUND!",
                "THE LAWS OF PHYSICS NO LONGER APPLY TO THIS COUPLE!", "GOD-TIER CONNECTION CONFIRMED.", "THE ARENA HAS ASCENDED TO A HIGHER PLANE.", "WE ARE WITNESSING A MIRACLE IN THE ARENA.", "INFINITY PERCENT COMPATIBILITY REACHED."
            ]
        }

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
            img = img.resize((380, 380)) 
            glow = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(glow)
            glow_color = (255, 69, 0, 220) if percentage > 50 else (180, 0, 255, 160)
            g_draw.ellipse([0, 0, 450, 450], fill=glow_color)
            glow = glow.filter(ImageFilter.GaussianBlur(35))
            return img, glow

        av1, glow1 = process_avatar(avatar1_bytes)
        av2, glow2 = process_avatar(avatar2_bytes)

        canvas.paste(glow1, (-35, 75), glow1)
        canvas.paste(av1, (0, 110), av1)
        canvas.paste(glow2, (785, 75), glow2)
        canvas.paste(av2, (820, 110), av2)

        # 4. REDESIGNED: Organic Light-Filled Column
        bar_x, bar_y, bar_w, bar_h = 420, 20, 360, 560
        
        col_glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cg_draw = ImageDraw.Draw(col_glow)
        cg_draw.rectangle([bar_x-20, bar_y-10, bar_x+bar_w+20, bar_y+bar_h+10], fill=(255, 50, 50, 40))
        col_glow = col_glow.filter(ImageFilter.GaussianBlur(20))
        canvas.paste(col_glow, (0, 0), col_glow)

        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(255, 255, 255, 15)) 
        
        fill_height = int((percentage / 100) * bar_h)
        fill_top_y = (bar_y + bar_h) - fill_height
        
        if fill_height > 5:
            for i in range(fill_top_y, bar_y + bar_h):
                intensity = int(180 + (i - fill_top_y) / (fill_height + 1) * 75)
                draw.line([(bar_x + 5, i), (bar_x + bar_w - 5, i)], fill=(100, intensity, 50, 200))

        # 5. MEGA ZOOMED PERCENTAGE LOGIC
        text_str = f"{percentage}%"
        text_canvas = Image.new('RGBA', (1000, 550), (0, 0, 0, 0))
        t_draw = ImageDraw.Draw(text_canvas)
        
        f_size = 380 
        try:
            font_pct = ImageFont.truetype("arial.ttf", f_size)
        except:
            try:
                font_pct = ImageFont.truetype("DejaVuSans-Bold.ttf", f_size)
            except:
                font_pct = ImageFont.load_default()

        t_draw.text((508, 278), text_str, fill=(255, 255, 255, 50), font=font_pct, anchor="mm")
        t_draw.text((500, 270), text_str, fill="white", font=font_pct, anchor="mm", stroke_width=16, stroke_fill="black")
        
        if font_pct.getbbox(text_str)[2] < 100: 
            text_canvas = text_canvas.resize((3000, 1600), Image.Resampling.NEAREST)
            canvas.paste(text_canvas, (-900, -500), text_canvas) 
        else:
            canvas.paste(text_canvas, (100, 50), text_canvas)

        # 6. ADDITION: 100% Special Heart Icon
        if percentage == 100:
            heart_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            h_draw = ImageDraw.Draw(heart_layer)
            h_draw.text((600, 310), "💎❤️💎", fill="white", font=font_pct, anchor="mm")
            canvas.paste(heart_layer, (0, 0), heart_layer)

        # Final labels
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

                # Tiered Message Logic
                if percentage <= 15: tier = "0-15"
                elif percentage <= 30: tier = "16-30"
                elif percentage <= 45: tier = "31-45"
                elif percentage <= 60: tier = "46-60"
                elif percentage <= 75: tier = "61-75"
                elif percentage <= 90: tier = "76-90"
                else: tier = "91-100"
                
                selected_msg = random.choice(self.arena_messages[tier])
                embed.description = f"**{selected_msg}**"

                if percentage == 0: status = "🧊 Absolute Zero - Ice Cold"
                elif percentage < 25: status = "💔 Broken Bonds - No Match"
                elif percentage < 50: status = "🤝 Just Friends - Casual"
                elif percentage < 75: status = "💖 Growing Spark - Hot"
                elif percentage < 100: status = "🔥 Eternal Flames - Perfection"
                else: status = "💎 UNSTOPPABLE DESTINY 💎"
                
                embed.set_footer(text=f"Arena Status: {status}")
                await ctx.send(file=file, embed=embed)
                
            except Exception as e:
                print(f"Error in Ship Command: {e}")
                await ctx.send("⚠️ An error occurred while generating the ship card. Check the console.")

    @commands.command(name="matchme")
    async def matchme(self, ctx):
        async with ctx.typing():
            try:
                members = [m for m in ctx.guild.members if not m.bot and m.id != ctx.author.id]
                if not members: return await ctx.send("⚠️ No arena contenders found!")
                matches = []
                today = datetime.now().strftime("%Y-%m-%d")
                for member in members:
                    seed = f"{ctx.author.id}{member.id}{today}"
                    random.seed(seed)
                    score = random.randint(1, 100)
                    matches.append((member, score))
                matches.sort(key=lambda x: x[1], reverse=True)
                top_5 = matches[:5]
                embed = discord.Embed(title="🔥 ARENA TENSION: TOP 5 MATCHES 🔥", description=f"Scanning the crowd for **{ctx.author.display_name}**'s perfect match...", color=0xFF4500)
                ranking_text = ""
                medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
                for i, (member, score) in enumerate(top_5):
                    intensity = "MAXIMUM" if score > 90 else "HIGH" if score > 70 else "WARM"
                    ranking_text += f"{medals[i]} **{member.display_name}** — **{score}%** `{intensity}`\n"
                embed.add_field(name="⚔️ Current Contenders", value=ranking_text, inline=False)
                if os.path.exists("fierylogo.jpg"):
                    file = discord.File("fierylogo.jpg", filename="fierylogo.jpg")
                    embed.set_thumbnail(url="attachment://fierylogo.jpg")
                    await ctx.send(file=file, embed=embed)
                else:
                    embed.set_thumbnail(url=ctx.author.display_avatar.url)
                    await ctx.send(embed=embed)
                random.seed()
            except Exception as e:
                print(f"Error: {e}")
                await ctx.send("⚠️ The Arena is too hot!")

async def setup(bot):
    await bot.add_cog(Ship(bot))
