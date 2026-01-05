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
            # 1. TRANSPARENT ENGINE (1200x600 for Max Embed Fit)
            canvas = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
            draw = ImageDraw.Draw(canvas)

            # --- FONT SYSTEM LOADER (COLOSSAL FIX - NO LIMITS) ---
            # Font size increased to 800+ for massive visibility now that the plate is gone
            font_size_pct = 850 if percent < 100 else 700 
            font_size_heart = 120
            try:
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                    "C:\\Windows\\Fonts\\arialbd.ttf",
                    "arial.ttf"
                ]
                font_file = next((f for f in font_paths if os.path.exists(f)), None)
                if font_file:
                    font_pct = ImageFont.truetype(font_file, font_size_pct)
                    font_heart = ImageFont.truetype(font_file, font_size_heart)
                else:
                    font_pct = ImageFont.load_default()
                    font_heart = ImageFont.load_default()
            except:
                font_pct = ImageFont.load_default()
                font_heart = ImageFont.load_default()
            
            # 2. PARTICLE GENERATOR (Skulls for Doom, Hearts for Glory)
            particle_count = 100 if percent >= 80 else 50
            for _ in range(particle_count):
                px, py = random.randint(0, 1200), random.randint(0, 600)
                p_size = random.randint(5, 18) if percent < 80 else random.randint(10, 25)
                if percent < 20:
                    draw.text((px, py), "💀", fill=(0, 255, 255, 100), font=font_heart)
                else:
                    p_color = (255, 105, 180, 160) if percent < 80 else (255, 215, 0, 180) 
                    draw.polygon([(px, py), (px+p_size, py-p_size), (px+p_size*2, py)], fill=p_color)

            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())

            av_size = 480
            av1_raw = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2_raw = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            # 3. DYNAMIC COLOR ENGINE
            if percent <= 50:
                ratio = percent / 50
                r = int(120 + (135 * ratio))
                g = int(120 - (120 * ratio))
                b = int(140 - (100 * ratio))
            else:
                ratio = (percent - 50) / 50
                r = 255
                g = int(50 * (1 - ratio) + 215 * ratio)
                b = int(100 * (1 - ratio))
            aura_color = (r, g, b)
            
            aura = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
            a_draw = ImageDraw.Draw(aura)
            a_draw.rectangle([40, 50, 40+av_size+10, 60+av_size+10], fill=(0, 0, 0, 180))
            a_draw.rectangle([700, 50, 710+av_size+10, 60+av_size+10], fill=(0, 0, 0, 180))
            a_draw.ellipse([20, 40, 60+av_size+30, 80+av_size+30], fill=(aura_color[0], aura_color[1], aura_color[2], 80))
            a_draw.ellipse([680, 40, 720+av_size+30, 80+av_size+30], fill=(aura_color[0], aura_color[1], aura_color[2], 80))
            aura = aura.filter(ImageFilter.GaussianBlur(35))
            canvas = Image.alpha_composite(canvas, aura)

            # Borders
            draw.rectangle([48, 58, 52+av_size, 62+av_size], outline=aura_color, width=12)
            draw.rectangle([708, 58, 712+av_size, 62+av_size], outline=aura_color, width=12)

            canvas.paste(av1_raw, (50, 60), av1_raw)
            canvas.paste(av2_raw, (710, 60), av2_raw)

            # 4. IMPERIAL BOND
            nova = Image.new("RGBA", (1200, 600), (0,0,0,0))
            ImageDraw.Draw(nova).ellipse([400, 100, 800, 500], fill=(255, 255, 255, 15))
            nova = nova.filter(ImageFilter.GaussianBlur(50))
            canvas = Image.alpha_composite(canvas, nova)

            # Love Column
            col_x, col_y, col_w, col_h = 585, 60, 30, 480
            draw.rounded_rectangle([col_x, col_y, col_x + col_w, col_y + col_h], radius=15, fill=(20, 0, 0, 180), outline=(255, 255, 255, 60), width=2)
            fill_size = int((percent / 100) * (col_h - 6))
            if fill_size > 0:
                draw.rounded_rectangle([col_x + 3, col_y + col_h - 3 - fill_size, col_x + col_w - 3, col_y + col_h - 3], radius=12, fill=(255, 0, 40, 220))

            # Logo
            if os.path.exists("fierylogo.jpg"):
                logo = Image.open("fierylogo.jpg").convert("RGBA").resize((135, 135))
                mask = Image.new("L", (135, 135), 0)
                ImageDraw.Draw(mask).ellipse([0, 0, 135, 135], fill=255)
                logo.putalpha(mask)
                canvas.paste(logo, (532, 35), logo)

            # --- 6. IMPERIAL GLOW FILTER ---
            glow = canvas.filter(ImageFilter.GaussianBlur(8))
            canvas = Image.alpha_composite(glow, canvas)

            # --- 7. FINAL OVERLAY: THE COLOSSAL SCORE (BACKGROUND PLATE DELETED) ---
            overlay = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
            o_draw = ImageDraw.Draw(overlay)
            
            if percent >= 90:
                text_main, text_stroke = (255, 255, 255), (255, 215, 0)
            elif percent >= 70:
                text_main, text_stroke = (255, 215, 0), (0, 0, 0)
            elif percent < 20:
                text_main, text_stroke = (139, 0, 0), (20, 0, 0)
            else:
                text_main, text_stroke = (255, 255, 255), (255, 105, 180) 

            pct_text = f"{percent}%"
            # COLOSSAL SHADOW FOR DEPTH
            o_draw.text((625, 325), pct_text, fill=(0, 0, 0, 255), anchor="mm", font=font_pct) 
            # COLOSSAL FOCAL SCORE - MAXIMUM POP
            o_draw.text((600, 300), pct_text, fill=text_main, anchor="mm", font=font_pct, stroke_width=60, stroke_fill=text_stroke)

            # Merging top layer last to ensure zero blurring and maximum size
            canvas = Image.alpha_composite(canvas, overlay)

            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Visual Error: {e}")
            return None

    @commands.command(name="ship")
    async def ship(self, ctx, member: discord.Member = None):
        if member is None:
            return await ctx.send("💘 **THE ORACLE NEEDS A PARTNER!** Mention someone to challenge the fates!")
        if member.id == ctx.author.id:
            return await ctx.send("🎭 Narcissus? Try shipping with someone else!")

        percent = random.randint(0, 100)
        fate_messages = [
            "✨ A match made in the celestial heavens!", "🏛️ The arena floor trembles at this bond.",
            "🔥 Two souls forged in the fires of destiny.", "👑 A romance the Emperors would envy.",
            "🌟 The stars align perfectly for this union.", "🧨 A spark that could ignite the entire arena.",
            "🥀 Tread carefully, for this bond is fragile.", "📜 A connection written in the ancient scrolls.",
            "💎 The fates whisper of a legendary pair.", "🧿 Even the gods are watching this duo.",
            "⚔️ An alliance that shall echo through time.", "🏹 Destiny has chosen its favorite pair.",
            "🕊️ A harmony that silences the colosseum.", "🔮 The Oracle foresees a powerful future.",
            "🛡️ Two hearts, one unbreakable battle cry."
        ]
        chosen_msg = random.choice(fate_messages)

        if percent >= 90: title = "👑 ABSOLUTE DYNASTY"
        elif percent >= 70: title = "💖 ETERNAL FLAME"
        elif percent >= 50: title = "⚖️ BALANCED DESTINY"
        elif percent >= 20: title = "☁️ FADING EMBERS"
        else: title = "💀 DOOMED ROMANCE"

        async with ctx.typing():
            ship_img = await self.create_ship_visual(ctx.author.display_avatar.url, member.display_avatar.url, percent)
            embed_color = 0xFFD700 if percent >= 90 else 0xFF4500 if percent >= 50 else 0x00FFFF if percent < 20 else 0x808080
            embed = discord.Embed(title=f"🏹 {title}", color=embed_color)
            embed.description = f"### {ctx.author.mention} 💓 {member.mention}\n\n> *{chosen_msg}*"
            if ship_img:
                file = discord.File(ship_img, filename="ship.png")
                embed.set_image(url="attachment://ship.png")
            embed.set_footer(text="Glory to the Echo! | Master Matchmaker", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            await ctx.send(file=file if ship_img else None, embed=embed)

    @commands.command(name="matchme")
    async def matchme(self, ctx):
        async with ctx.typing():
            potential_members = [m for m in ctx.guild.members if not m.bot and m.id != ctx.author.id]
            if not potential_members:
                return await ctx.send("❌ No gladiators found in this arena!")
            
            sample_size = min(len(potential_members), 15)
            sample = random.sample(potential_members, sample_size)
            matches = [(m, random.randint(1, 100)) for m in sample]
            matches.sort(key=lambda x: x[1], reverse=True)
            top_5 = matches[:5]

            embed = discord.Embed(title="🔥 ARENA MATCHMAKER", description=f"Gladiator {ctx.author.mention}, the fates have spoken:", color=0xFF4500)
            if os.path.exists("fierylogo.jpg"):
                logo_file = discord.File("fierylogo.jpg", filename="logo.png")
                embed.set_thumbnail(url="attachment://logo.png")
            
            results_text = ""
            for i, (member, score) in enumerate(top_5, 1):
                indicator = "💖" if score >= 90 else "🔥" if score >= 70 else "⚖️" if score >= 50 else "✨"
                results_text += f"**{i}. {member.display_name}** — {score}% {indicator}\n"
            
            embed.add_field(name="🏛️ TOP POTENTIAL MATCHES", value=results_text, inline=False)
            embed.set_footer(text="Glory to the Echo! | Try !ship with them.", icon_url=ctx.author.display_avatar.url)
            
            await ctx.send(file=logo_file if os.path.exists("fierylogo.jpg") else None, embed=embed)

async def setup(bot):
    await bot.add_cog(DungeonShip(bot))
