import discord
from discord.ext import commands
import random
import io
import aiohttp
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import __main__

class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Database Setup for Top Ships
        self.conn = sqlite3.connect('ships.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ship_history 
                              (user_id INTEGER, target_id INTEGER, target_name TEXT, percentage INTEGER, timestamp DATETIME)''')
        self.conn.commit()

        # 175 Heartfelt Messages Tiered by Percentage (Expanded Again)
        self.arena_messages = {
            "0-15": [
                "The sanctuary is freezing over. Total mismatch.", "Ice cold. Not even a spark found.", "Kindness is escorting you both to different paths.", "The angels are sighing. This is a distance.", "Error 404: Love not found in this sanctuary.", 
                "A black hole has more attraction than this.", "The tension is quiet. Please stop.", "Even the heartbeats slowed looking at you two.", "Zero chemistry detected. Move along.", "This isn't a ship, it's a quiet harbor.", 
                "You two are on different planets.", "The sanctuary candles just flickered and died.", "Total silence from the souls. Awkward.", "A bond made in... well, not here.", "Better luck in the next life.",
                "The Love announcer is speechless at how quiet this is.", "A cactus has a softer touch than this pairing.", "The simulation crashed trying to find connection.", "The matchmakers left because there is zero heat.", "Total soul rejection.",
                "The hearts are turning away. Please leave.", "A magnetic field of identical poles. Total repulsion.", "The ship sank before it even left the dock.", "Absolute zero. Science cannot explain this void.", "Even the bot feels second-hand sadness."
            ],
            "16-30": [
                "Slight friction, but mostly just sparks of shyness.", "The sanctuary remains mostly dark.", "Maybe try talking? Or maybe don't.", "A very weak connection detected.", "The hearts are drifting elsewhere.", 
                "Not exactly a dream couple.", "Room for improvement... a lot of it.", "The love meter barely moved.", "A flicker in the dark, then nothing.", "You're both better off as solo travelers.", 
                "The sanctuary floor is still cold.", "Minimal compatibility found.", "Are you even trying?", "The fire is struggling to start.", "A distant 'maybe' at best.",
                "The Sanctuary gardener is more excited than you two.", "Static on the line. Too much interference.", "The moonlight is trying to find you, but it's bored.", "Like oil and water in a blender.", "A flicker of hope, but mostly just smoke.",
                "The sparks are trying, but the fuel is damp.", "A very quiet day in the Love Sanctuary.", "Connection level: Casual acquaintances.", "You're both in the friendzone's basement.", "The Sanctuary lights are dimming in disappointment."
            ],
            "31-45": [
                "The embers are starting to glow.", "A gentle friendship, nothing more.", "The sanctuary is lukewarm.", "Friends with sweet benefits?", "Not a total loss, but not a win.", 
                "The hearts are curious, but not convinced.", "A steady beat, but no rhythm yet.", "You won't break each other... probably.", "Just enough to keep the lights on.", "The sanctuary is waiting for more.", 
                "A mild interest detected.", "Stable, but soft.", "The ship is floating, but not moving.", "Testing the waters of the heart.", "A low-level bond.",
                "The Sanctuary spectators are leaning in slightly.", "A spark exists, but needs a lot of oxygen.", "Walking the line between friends and admirers.", "The foundation is there, but the house is empty.", "Lukewarm tea levels of passion.",
                "The tension is starting to crackle.", "A decent team-up, but is it love?", "The Sanctuary radar is picking up a signal.", "Moderately compatible, mostly just polite.", "The embers are whispering, not shouting."
            ],
            "46-60": [
                "The sanctuary is heating up!", "A solid match for the mid-tier.", "The hearts are starting to cheer.", "Balanced soul levels.", "The sparks are consistent now.", 
                "A beautiful dance in the sanctuary.", "The tension is palpable.", "Halfway to destiny.", "The fire is growing steady.", "You look good together under the lights.", 
                "A promising future in the sanctuary.", "The chemistry is becoming visible.", "Keep this energy going.", "A match worth watching.", "The sanctuary floor is warming up.",
                "The souls are starting to celebrate you two.", "Synchronized hearts in the game of love.", "A powerful rhythm is taking over the Sanctuary.", "You're making the front row smile.", "The heat is finally real.",
                "The Love Sanctuary is officially interested.", "A strong foundation for a Sanctuary power couple.", "The sparks are becoming small flames.", "Consistency is key, and you've got it.", "The stadium hums with your combined energy."
            ],
            "61-75": [
                "Intense energy flowing through the sanctuary!", "The hearts are on their feet!", "A high-tier pairing detected.", "The sparks are flying everywhere.", "The sanctuary is glowing bright pink.", 
                "A passionate dance of hearts.", "Almost at the peak of the sanctuary.", "The love tension is rising fast.", "The embers are turning into flames.", "A powerful connection is forming.", 
                "The stadium is roaring for you two.", "Strongest match of the hour!", "The sanctuary lights are pulsing.", "Destined for something great.", "True love synergy.",
                "The Sanctuary screens are flashing 'WARNING: RADIANT LOVE'.", "Your souls are resonant at a high frequency.", "The ground is literally shaking now.", "A beautiful storm is brewing in the center.", "Pure, unadulterated heart magnetism.",
                "The Sanctuary is glowing with your potential.", "A high-voltage connection that lights up the sky.", "Passion is the primary fuel here.", "The angels are giving you a standing ovation.", "A match that threatens to melt the Sanctuary floor."
            ],
            "76-90": [
                "The sanctuary is on fire!", "A legendary pairing has entered.", "The love tension is reaching critical levels!", "Breathtaking compatibility.", "The hearts are calling your names!", 
                "Electric. Passionate. Unstoppable.", "A high-voltage soul match.", "The heat is nearly unbearable!", "Almost perfect. Simply beautiful.", "The stadium is shaking from the tension.", 
                "A match for the ages.", "Burning brighter than the sun.", "The sanctuary has never seen this before.", "Soulmate territory found.", "Pure heart magic.",
                "The Sanctuary ceiling is about to blow off!", "Gravity is failing because of your attraction.", "A masterclass in romantic chemistry.", "The embers have become a localized sun.", "Elite tier compatibility achieved.",
                "The Love Sanctuary hasn't seen this much heat in years!", "A connection so strong it's distorting the spotlight.", "Absolute fireworks in every direction.", "You are the undisputed champions of the night.", "A bond forged in the hottest Sanctuary fires."
            ],
            "91-100": [
                "THE SANCTUARY HAS EXPLODED! TRUE LOVE!", "A DIVINE MATCH MADE IN THE HEAVENS!", "ULTIMATE COMPATIBILITY DETECTED!", "THE LOVE SANCTUARY IS IN TOTAL SHOCK!", "A PERFECT HARMONY OF SOULS!", 
                "BEYOND LEGENDARY. BEYOND PERFECTION.", "THE DESTINY METER JUST BROKE!", "UNSTOPPABLE SOUL POWER!", "THE HEARTS ARE WEEPING FROM JOY!", "A MATCH THAT WILL BE REMEMBERED FOREVER!", 
                "TOTAL SANCTUARY DOMINATION BY LOVE!", "THE EMBERS HAVE TURNED INTO A SUPERNOVA!", "YOU ARE THE KINGS OF THE LOVE SANCTUARY!", "A DIAMOND IN THE ROUGH? NO, A DIAMOND HEART!", "ABSOLUTE PERFECTION FOUND!",
                "THE LAWS OF PHYSICS NO LONADY APPLY TO THIS COUPLE!", "GOD-TIER CONNECTION CONFIRMED.", "THE ARENA HAS ASCENDED TO A HIGHER PLANE.", "WE ARE WITNESSING A MIRACLE IN THE SANCTUARY.", "INFINITY PERCENT COMPATIBILITY REACHED.",
                "THE SANCTUARY IS MELTING INTO PURE GOLD.", "THE HEARTS OF THE AUDIENCE HAVE BECOME ONE WITH YOURS.", "A MATCH SO BRIGHT IT BLINDS THE SPECTATORS.", "ETERNAL CHAMPIONS OF THE HEART.", "THE UNIVERSE ITSELF CHEERS FOR YOU TWO."
            ]
        }

    def check_premium(self, guild_id):
        # Access global PREMIUM_GUILDS from main.py
        now = datetime.now(timezone.utc).timestamp()
        guild_id_str = str(guild_id)
        premium_data = getattr(__main__, 'PREMIUM_GUILDS', {})
        
        # Check if guild is in list and if 'ship' module is active and not expired
        guild_mods = premium_data.get(guild_id_str, {})
        expiry = guild_mods.get('ship', 0)
        
        return expiry > now

    def create_ship_card(self, avatar1_bytes, avatar2_bytes, percentage):
        width, height = 1200, 600
        canvas = Image.new('RGB', (width, height), color='#2c0003')
        draw = ImageDraw.Draw(canvas, "RGBA")
        
        # 1. ENHANCED: Background Love Sanctuary Gradient
        for i in range(height):
            r = int(40 + (i / height) * 90)
            g = int(0 + (i / height) * 20)
            draw.line([(0, i), (width, i)], fill=(r, g, 10))

        # ADDITION: Center Spotlight Glow (Sanctuary Effect)
        spotlight = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(spotlight)
        for r in range(1, 500, 5):
            alpha = int(100 * (1 - r / 500))
            s_draw.ellipse([600-r, 300-r, 600+r, 300+r], outline=(255, 50, 50, alpha))
        canvas.paste(spotlight, (0, 0), spotlight)

        # 2. ENHANCED: High-Intensity Love Particles (Embers)
        for _ in range(80): 
            p_x = random.randint(0, width)
            p_y = random.randint(0, height)
            p_size = random.randint(2, 8)
            p_color = random.choice([(255, 182, 193, 160), (255, 105, 180, 180), (255, 255, 255, 120)])
            draw.ellipse([p_x, p_y, p_x + p_size, p_y + p_size], fill=p_color)

        # 3. Avatar Processing - ZOOMED & NO BORDERS (380x380)
        def process_avatar(avatar_bytes):
            img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            img = img.resize((380, 380)) 
            glow = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(glow)
            
            # Special logic for 69% (Mischievous Glow)
            if percentage == 69:
                glow_color = (255, 20, 147, 230) 
            else:
                glow_color = (255, 105, 180, 220) if percentage > 50 else (180, 0, 255, 160)
                
            g_draw.ellipse([0, 0, 450, 450], fill=glow_color)
            glow = glow.filter(ImageFilter.GaussianBlur(35))
            return img, glow

        av1, glow1 = process_avatar(avatar1_bytes)
        av2, glow2 = process_avatar(avatar2_bytes)

        canvas.paste(glow1, (-35, 75), glow1)
        canvas.paste(av1, (0, 110), av1)
        canvas.paste(glow2, (785, 75), glow2)
        canvas.paste(av2, (820, 110), av2)

        # 4. REFINED: High-Intensity Dynamic Column - SOFT PINK CRYSTAL
        bar_x, bar_y, bar_w, bar_h = 490, 20, 220, 560
        
        col_glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cg_draw = ImageDraw.Draw(col_glow)
        cg_draw.rectangle([bar_x-15, bar_y, bar_x+bar_w+15, bar_y+bar_h], fill=(255, 182, 193, 30))
        col_glow = col_glow.filter(ImageFilter.GaussianBlur(20))
        canvas.paste(col_glow, (0, 0), col_glow)

        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(20, 5, 10, 190)) 
        
        fill_height = int((percentage / 100) * bar_h)
        fill_top_y = (bar_y + bar_h) - fill_height
        
        main_color = (255, 182, 193) # Light Pink

        if fill_height > 5:
            for i in range(fill_top_y, bar_y + bar_h):
                shimmer = int(30 * random.random())
                r, g, b = main_color
                draw.line([(bar_x + 10, i), (bar_x + bar_w - 10, i)], fill=(r, g + shimmer, b + shimmer, 240))

            core_w = bar_w // 5
            draw.rectangle([bar_x + (bar_w//2) - core_w, fill_top_y, bar_x + (bar_w//2) + core_w, bar_y + bar_h], fill=(255, 255, 255, 110))

        # 5. REFINED: NEON PERCENTAGE DISPLAY (Zoomed & Pink Glow)
        text_str = f"{percentage}%"
        text_canvas = Image.new('RGBA', (1000, 550), (0, 0, 0, 0))
        t_draw = ImageDraw.Draw(text_canvas)
        
        f_size = 450 
        try:
            font_pct = ImageFont.truetype("arial.ttf", f_size)
        except:
            try:
                font_pct = ImageFont.truetype("DejaVuSans-Bold.ttf", f_size)
            except:
                font_pct = ImageFont.load_default()

        glow_color = (255, 20, 147, 160) if percentage == 69 else (255, 182, 193, 140)
        t_draw.text((500, 270), text_str, fill=glow_color, font=font_pct, anchor="mm", stroke_width=35)
        text_canvas = text_canvas.filter(ImageFilter.GaussianBlur(15))
        
        t_draw = ImageDraw.Draw(text_canvas)
        t_draw.text((500, 270), text_str, fill="white", font=font_pct, anchor="mm", stroke_width=20, stroke_fill="black")
        
        if font_pct.getbbox(text_str)[2] < 100: 
            text_canvas = text_canvas.resize((3000, 1600), Image.Resampling.NEAREST)
            canvas.paste(text_canvas, (-900, -500), text_canvas) 
        else:
            canvas.paste(text_canvas, (100, 25), text_canvas)

        # 6. 100% Special Heart Icon
        if percentage == 100:
            heart_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            h_draw = ImageDraw.Draw(heart_layer)
            h_draw.text((600, 310), "💎❤️💎", fill="white", font=font_pct, anchor="mm")
            canvas.paste(heart_layer, (0, 0), heart_layer)

        # Final labels
        try:
            font_sub = ImageFont.truetype("arial.ttf", 60)
            draw.text((600, 40), "❤️ LOVE SANCTUARY ❤️", fill="#FFCC00", font=font_sub, anchor="mm", stroke_width=5, stroke_fill="black")
        except:
            draw.text((600, 40), "LOVE SANCTUARY", fill="#FFCC00", anchor="mm")

        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @commands.command(name="ship")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member = None):
        # PREMIUM CHECK
        if not self.check_premium(ctx.guild.id):
            embed = discord.Embed(title="🔒 MODULE LOCKED", color=0xff0000)
            embed.description = "The **LOVE** module is not active for this server. An administrator must use `!premium` to unlock high-tier sanctuary features."
            return await ctx.send(embed=embed)

        if user2 is None:
            user2 = user1
            user1 = ctx.author

        async with ctx.typing():
            try:
                percentage = random.randint(0, 100)

                # Log to History for !topship
                self.cursor.execute("INSERT INTO ship_history VALUES (?, ?, ?, ?, ?)", 
                                   (ctx.author.id, user2.id, user2.display_name, percentage, datetime.now()))
                self.conn.commit()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(user1.display_avatar.url)) as resp1:
                        if resp1.status != 200: raise Exception("Failed to get User1 Avatar")
                        av1_data = await resp1.read()
                    async with session.get(str(user2.display_avatar.url)) as resp2:
                        if resp2.status != 200: raise Exception("Failed to get User2 Avatar")
                        av2_data = await resp2.read()

                image_buffer = self.create_ship_card(av1_data, av2_data, percentage)
                
                file = discord.File(fp=image_buffer, filename="ship_result.png")
                embed = discord.Embed(title="💕 The Love Sanctuary Result 💕", color=0xff69b4)
                embed.set_image(url="attachment://ship_result.png")

                if percentage <= 15: tier = "0-15"
                elif percentage <= 30: tier = "16-30"
                elif percentage <= 45: tier = "31-45"
                elif percentage <= 60: tier = "46-60"
                elif percentage <= 75: tier = "61-75"
                elif percentage <= 90: tier = "76-90"
                else: tier = "91-100"
                
                selected_msg = random.choice(self.arena_messages[tier])
                if percentage == 69:
                    selected_msg = "A mischievous spark is in the air! Naughty and nice in perfect balance. 😏"
                
                embed.description = f"**{selected_msg}**"

                if percentage == 0: status = "🧊 Absolute Zero - Ice Cold"
                elif percentage == 69: status = "😏 MISCHIEVOUS SPARK - OH MY! 😏"
                elif percentage < 25: status = "💔 Broken Bonds - No Match"
                elif percentage < 50: status = "🤝 Just Friends - Casual"
                elif percentage < 75: status = "💖 Growing Spark - Sweet"
                elif percentage < 100: status = "🔥 Eternal Flames - Perfection"
                else: status = "💎 SOULMATE SUPREME - UNSTOPPABLE DESTINY 💎"
                
                embed.set_footer(text=f"Sanctuary Status: {status}")
                await ctx.send(file=file, embed=embed)
                
            except Exception as e:
                print(f"Error in Ship Command: {e}")
                await ctx.send("⚠️ An error occurred while generating the love card.")

    @commands.command(name="topship")
    async def topship(self, ctx):
        # PREMIUM CHECK
        if not self.check_premium(ctx.guild.id):
            embed = discord.Embed(title="🔒 MODULE LOCKED", color=0xff0000)
            embed.description = "The **LOVE** module is not active for this server. Use `!premium` to unlock."
            return await ctx.send(embed=embed)

        async with ctx.typing():
            try:
                thirty_days_ago = datetime.now() - timedelta(days=30)
                self.cursor.execute("""SELECT target_name, MAX(percentage) FROM ship_history 
                                     WHERE user_id = ? AND timestamp > ? 
                                     GROUP BY target_id ORDER BY MAX(percentage) DESC LIMIT 5""", 
                                  (ctx.author.id, thirty_days_ago))
                results = self.cursor.fetchall()

                embed = discord.Embed(title="💖 YOUR TOP CONNECTIONS (30 DAYS) 💖", color=0xff69b4)
                if not results:
                    embed.description = "You haven't set sail with anyone in the Sanctuary yet!"
                else:
                    medals = ["🥇", "🥈", "🥉", "✨", "✨"]
                    text = ""
                    for i, (name, pct) in enumerate(results):
                        text += f"{medals[i]} **{name}** — **{pct}%**\n"
                    embed.description = text
                
                await ctx.send(embed=embed)
            except Exception as e:
                print(f"Topship Error: {e}")
                await ctx.send("⚠️ Unable to retrieve your Sanctuary history.")

    @commands.command(name="matchme")
    async def matchme(self, ctx):
        if not self.check_premium(ctx.guild.id):
            embed = discord.Embed(title="🔒 MODULE LOCKED", color=0xff0000)
            embed.description = "The **LOVE** module is not active for this server. Use `!premium` to unlock."
            return await ctx.send(embed=embed)

        async with ctx.typing():
            try:
                members = [m for m in ctx.guild.members if not m.bot and m.id != ctx.author.id]
                if not members: return await ctx.send("⚠️ No kindred souls found!")
                matches = []
                today = datetime.now().strftime("%Y-%m-%d")
                for member in members:
                    seed = f"{ctx.author.id}{member.id}{today}"
                    random.seed(seed)
                    score = random.randint(1, 100)
                    matches.append((member, score))
                matches.sort(key=lambda x: x[1], reverse=True)
                top_5 = matches[:5]
                embed = discord.Embed(title="✨ KINDRED SPIRITS: TOP 5 MATCHES ✨", description=f"Scanning the hearts for **{ctx.author.display_name}**'s perfect match...", color=0xff69b4)
                ranking_text = ""
                medals = ["❤️", "🧡", "💛", "💚", "💙"]
                for i, (member, score) in enumerate(top_5):
                    intensity = "MAXIMUM" if score > 90 else "HIGH" if score > 70 else "SWEET"
                    ranking_text += f"{medals[i]} **{member.display_name}** — **{score}%** `{intensity}`\n"
                embed.add_field(name="💞 Kindred Souls", value=ranking_text, inline=False)
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
                await ctx.send("⚠️ The Sanctuary is too warm!")

async def setup(bot):
    await bot.add_cog(Ship(bot))
async def setup(bot):
    await bot.add_cog(Ship(bot))
