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

class DungeonFight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module_name = "fight"
        # Persistent Data Storage
        self.stats_file = "/app/data/fight_stats.json"
        self._load_stats()
        # Battle log history tracking
        self.battle_histories = {}

    def _load_stats(self):
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, "r") as f:
                    self.stats = json.load(f)
            else:
                self.stats = {"global": {}, "servers": {}}
        except Exception as e:
            print(f"Error loading stats: {e}")
            self.stats = {"global": {}, "servers": {}}

    def _save_stats(self):
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, "w") as f:
                json.dump(self.stats, f, indent=4)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def _update_winner(self, guild_id, winner_id, loser_id):
        gid = str(guild_id)
        wid = str(winner_id)
        lid = str(loser_id)

        # Global Update
        if wid not in self.stats["global"]:
            self.stats["global"][wid] = {"wins": 0, "fights": 0, "streak": 0, "victims": {}}
        if lid not in self.stats["global"]:
            self.stats["global"][lid] = {"wins": 0, "fights": 0, "streak": 0, "victims": {}}
            
        self.stats["global"][wid]["wins"] += 1
        self.stats["global"][wid]["fights"] += 1
        self.stats["global"][wid]["streak"] += 1
        self.stats["global"][lid]["fights"] += 1
        self.stats["global"][lid]["streak"] = 0 # Reset loser streak
        self.stats["global"][wid]["victims"][lid] = self.stats["global"][wid]["victims"].get(lid, 0) + 1

        # Local Update
        if gid not in self.stats["servers"]:
            self.stats["servers"][gid] = {}
        if wid not in self.stats["servers"][gid]:
            self.stats["servers"][gid][wid] = {"wins": 0, "fights": 0, "streak": 0, "victims": {}}
        if lid not in self.stats["servers"][gid]:
            self.stats["servers"][gid][lid] = {"wins": 0, "fights": 0, "streak": 0, "victims": {}}

        self.stats["servers"][gid][wid]["wins"] += 1
        self.stats["servers"][gid][wid]["fights"] += 1
        self.stats["servers"][gid][wid]["streak"] += 1
        self.stats["servers"][gid][lid]["fights"] += 1
        self.stats["servers"][gid][lid]["streak"] = 0 # Reset loser streak
        self.stats["servers"][gid][wid]["victims"][lid] = self.stats["servers"][gid][wid]["victims"].get(lid, 0) + 1
        
        self._save_stats()

    def get_health_bar(self, hp, max_hp, is_premium):
        pct = (hp / max_hp) * 100
        # Color Logic: Green (100-55%) > Yellow (54-25%) > Red (24-0%)
        if pct >= 55: segment = "🟩"
        elif pct >= 25: segment = "🟨"
        else: segment = "🟥"
        
        # Dynamic Segmented Bar (10 segments)
        filled = max(0, min(10, int(pct / 10)))
        empty = 10 - filled
        bar_str = segment * filled + "⬛" * empty
        
        return f"**{bar_str}** {pct:.0f}% ({hp}/{max_hp} HP)"

    def get_funny_msg(self, action_type):
        msgs = {
            "strike": [
                "swung a wet noodle at", "delivered a legendary slap to", "poked the eye of", "threw a heavy dictionary at",
                "used a gamer move on", "challenged the physics of the universe hitting", "sent a strongly worded email to the face of",
                "tried to delete the existence of", "performed a professional wrestling dropkick on", "threw a spoiled slice of pizza at",
                "whispered an embarrassing secret to distract", "bonked the head of", "accidentally sneezed too hard on",
                "used a selfie stick as a spear against", "threw a handful of glitter into the eyes of", "attempted a 360-no-scope slap on",
                "lightly tapped the shoulder of", "summoned a tiny, angry pigeon to peck", "dropped a massive piano (cartoon style) on",
                "hit a home run using the head of", "summoned a bolt of lightning against", "charged like a centurion at",
                "unleashed the fury of the gods on", "kicked into a bottomless pit (Sparta style)", "dealt a critical vibe check to"
            ],
            "heal": [
                "ate a suspicious mushroom.", "drank a glowing potion that tastes like blueberry.", "took a quick napped mid-battle.",
                "used a band-aid on a broken heart.", "screamed 'I REFUSE TO DIE' and felt better.",
                "found a half-eaten sandwich on the floor.", "rubbed some dirt on the wound.", "recalled a happy memory and gained life.",
                "drank some spicy lava juice.", "patched themselves up with duct tape.", "received a magical high-five from a ghost.",
                "consumed an entire wheel of cheese instantly.", "activated 'Main Character' plot armor.",
                "took a sip of a very expensive energy drink.", "prayed to the gods of the Echo.", "did a quick yoga pose to realign their soul."
            ]
        }
        return random.choice(msgs[action_type])

    # --- IMAGE ENGINE FOR ARENA VISUALS ---
    async def create_arena_visual(self, u1_url, u2_url, p1_hp, p2_hp):
        try:
            # Create a base canvas
            canvas = Image.new("RGBA", (1200, 600), (40, 0, 0, 255))
            
            # Roman Empire Cinematic Background (Adjusted for centering)
            if os.path.exists("fight.jpg"):
                bg = Image.open("fight.jpg").convert("RGBA")
                # Resize slightly larger to allow "shifting" the background to center the sword
                bg = bg.resize((1400, 600)) 
                # Paste with -100 offset to shift the image right compared to previous -50
                canvas.paste(bg, (-100, 0))
            
            draw = ImageDraw.Draw(canvas)
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())
            
            av_size = 380 
            av1_raw = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2_raw = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

            # PROFESSIONAL AVATAR FITTING: Circle masks with gold borders
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, av_size, av_size], fill=255)

            av1 = ImageOps.fit(av1_raw, mask.size, centering=(0.5, 0.5))
            av1.putalpha(mask)
            av2 = ImageOps.fit(av2_raw, mask.size, centering=(0.5, 0.5))
            av2.putalpha(mask)

            # UI Platforms Logic (Match Image Style)
            draw.rectangle([50, 480, 500, 530], fill=(52, 152, 219, 230)) # Blue platform P1
            draw.rectangle([700, 480, 1150, 530], fill=(231, 76, 60, 230)) # Red platform P2

            lighting = Image.new("RGBA", (1200, 600), (0,0,0,0))
            ImageDraw.Draw(lighting).polygon([(0,0), (1200,0), (600,600)], fill=(255, 69, 0, 30)) 

            # Paste Avatars with Gold Frame Ellipses
            p1_pos, p2_pos = (85, 80), (735, 80)
            draw.ellipse([p1_pos[0]-10, p1_pos[1]-10, p1_pos[0]+av_size+10, p1_pos[1]+av_size+10], outline=(212, 175, 55), width=12)
            draw.ellipse([p2_pos[0]-10, p2_pos[1]-10, p2_pos[0]+av_size+10, p2_pos[1]+av_size+10], outline=(212, 175, 55), width=12)
            
            canvas.paste(av1, p1_pos, av1)
            canvas.paste(av2, p2_pos, av2)
            canvas = Image.alpha_composite(canvas, lighting)
            draw = ImageDraw.Draw(canvas)

            # Status Icons (Trophy/RIP) Logic
            if p2_hp <= 0:
                draw.text((275, 420), "🏆", font=None, size=80, anchor="mm")
                draw.text((925, 420), "🪦", font=None, size=80, anchor="mm")
            elif p1_hp <= 0:
                draw.text((275, 420), "🪦", font=None, size=80, anchor="mm")
                draw.text((925, 420), "🏆", font=None, size=80, anchor="mm")

            draw.text((600, 80), "ARENA FIGHT!", fill=(255, 255, 255), anchor="mm", stroke_width=2, stroke_fill=(0,0,0))
            draw.text((600, 280), "VS", fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(0,0,0))
            
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except:
            return None

    # --- WINNER CARD ENGINE ---
    async def create_winner_card(self, winner_url, name, g_wins, g_streak, l_wins, l_streak):
        try:
            # Enlarged Canvas for High-Impact Visuals
            card = Image.new("RGBA", (1200, 600), (15, 15, 15, 255))
            draw = ImageDraw.Draw(card)
            if os.path.exists("fierylogo.jpg"):
                logo = Image.open("fierylogo.jpg").convert("RGBA").resize((1200, 600))
                card.paste(logo, (0, 0))

            async with aiohttp.ClientSession() as session:
                async with session.get(winner_url) as r:
                    av_data = io.BytesIO(await r.read())
            
            # Big Avatar Framing
            av = Image.open(av_data).convert("RGBA").resize((450, 450))
            mask = Image.new("L", (450, 450), 0)
            ImageDraw.Draw(mask).ellipse((10, 10, 440, 440), fill=255)
            av.putalpha(mask)
            
            # Draw Gold Avatar Glow
            draw.ellipse((45, 70, 505, 530), outline=(255, 215, 0), width=15)
            card.paste(av, (50, 75), av)

            # Textual Data Section
            draw.text((580, 80), "ARENA CHAMPION", fill=(255, 215, 0))
            draw.text((580, 140), name.upper(), fill=(255, 255, 255))
            
            # Stat Blocks
            draw.text((580, 240), "🌍 GLOBAL DOMINATION", fill=(200, 200, 200))
            draw.text((580, 280), f"Conquests: {g_wins}  |  Streak: {g_streak} 🔥", fill=(255, 69, 0))
            
            draw.text((580, 380), "🏰 LOCAL SERVER GLORY", fill=(200, 200, 200))
            draw.text((580, 420), f"Conquests: {l_wins}  |  Streak: {l_streak} ⚔️", fill=(52, 152, 219))
            
            buf = io.BytesIO()
            card.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except:
            return None

    @commands.command(name="fight")
    async def fight(self, ctx, member: discord.Member = None):
        if member is None:
            return await ctx.send("❌ **THE ARENA DEMANDS A TRIBUTE!** Mention someone to challenge them!")
        if member.id == ctx.author.id:
            return await ctx.send("💢 You can't fight yourself.")
        if member.bot:
            return await ctx.send("🤖 Bots don't feel pain.")

        guild_id = str(ctx.guild.id)
        is_premium = False
        if hasattr(__main__, "PREMIUM_GUILDS") and guild_id in __main__.PREMIUM_GUILDS:
            is_premium = True

        p1 = {"user": ctx.author, "hp": 100, "max": 100, "luck": 1.0}
        p2 = {"user": member, "hp": 100, "max": 100, "luck": 1.0}
        turn, other = p1, p2
        # Setup history for the duel
        history = ["🏛️ **THE GATES OPEN!** The crowd roars as the fight begins."]
        self.battle_histories[ctx.channel.id] = history

        arena_img = await self.create_arena_visual(p1['user'].display_avatar.url, p2['user'].display_avatar.url, p1['hp'], p2['hp'])
        arena_file = discord.File(arena_img, filename="arena.png")
        embed = discord.Embed(title="🦅 IMPERIAL ARENA: A DUEL TO THE DEATH", color=0x8B0000)
        embed.set_image(url="attachment://arena.png")
        main_msg = await ctx.send(file=arena_file, embed=embed)

        while p1["hp"] > 0 and p2["hp"] > 0:
            await asyncio.sleep(3.0) 
            action = random.choices(["strike", "heal"], weights=[90, 10])[0]
            
            if action == "strike":
                dmg = int(random.randint(12, 28) * turn["luck"])
                other["hp"] = max(0, other["hp"] - dmg)
                msg = f"🗡️ **{turn['user'].display_name}** {self.get_funny_msg('strike')} **{other['user'].display_name}**, dealing **-{dmg}** damage!"
                emb_color = 0xFF4500 if dmg > 20 else 0x8B0000
            else:
                amt = random.randint(10, 22)
                turn["hp"] = min(turn["max"], turn["hp"] + amt)
                msg = f"🏺 **{turn['user'].display_name}** {self.get_funny_msg('heal')} (+{amt} HP)"
                emb_color = 0x50C878

            # Update history list to keep last 4
            history.append(msg)
            if len(history) > 4:
                history.pop(0)
            battle_log = "\n".join([f"> *{m}*" for m in history])

            arena_img = await self.create_arena_visual(p1['user'].display_avatar.url, p2['user'].display_avatar.url, p1['hp'], p2['hp'])
            arena_file = discord.File(arena_img, filename="arena.png")

            embed = discord.Embed(title=f"🏆 Victory! {turn['user'].display_name} was victorious!" if other["hp"] <= 0 else "🏟️ THE COLOSSEUM RADIATES GLORY", color=emb_color)
            embed.set_image(url="attachment://arena.png")
            embed.add_field(name=f"🔵 {p1['user'].display_name}", value=self.get_health_bar(p1['hp'], p1['max'], is_premium), inline=False)
            embed.add_field(name=f"🔴 {p2['user'].display_name}", value=self.get_health_bar(p2['hp'], p2['max'], is_premium), inline=False)
            embed.add_field(name="📜 BATTLE LOG", value=battle_log, inline=False)
            embed.set_footer(text=f"🚩 Turn: {turn['user'].display_name.upper()} | Glory to the Echo!")

            await main_msg.edit(attachments=[arena_file], embed=embed)
            if other["hp"] <= 0: break
            turn, other = other, turn

        winner = turn if turn["hp"] > 0 else other
        loser = other if turn["hp"] > 0 else turn
        self._update_winner(ctx.guild.id, winner["user"].id, loser["user"].id)

        # Pull detailed stats for Winner Card
        wid_str = str(winner["user"].id)
        gid_str = str(ctx.guild.id)
        g_stats = self.stats["global"].get(wid_str, {"wins": 0, "streak": 0})
        l_stats = self.stats["servers"].get(gid_str, {}).get(wid_str, {"wins": 0, "streak": 0})

        win_card_buf = await self.create_winner_card(winner["user"].display_avatar.url, winner["user"].display_name, g_stats["wins"], g_stats["streak"], l_stats["wins"], l_stats["streak"])
        if win_card_buf:
            await ctx.send(file=discord.File(win_card_buf, filename="winner_card.png"), embed=discord.Embed(title="🏆 THE ETERNAL CHAMPION", color=0xFFD700).set_image(url="attachment://winner_card.png"))

    @commands.command(name="fightrank")
    async def fightrank(self, ctx, user: discord.Member = None):
        target = user or ctx.author
        tid = str(target.id)
        g_data = self.stats["global"].get(tid, {"wins": 0, "streak": 0, "fights": 0, "victims": {}})
        
        # Calculation for Valor Ratio
        total_fights = g_data.get("fights", 0)
        total_wins = g_data.get("wins", 0)
        ratio = (total_wins / total_fights * 100) if total_fights > 0 else 0
        
        embed = discord.Embed(title=f"📜 THE SCROLLS OF VALOR: {target.display_name.upper()}", color=0xFF4500)
        embed.description = f"⚔️ **Imperial Gladiator Profile**\n*Glory to the Echo!*"
        
        # Fiery Logo Thumbnail Logic
        logo_file = None
        if os.path.exists("fierylogo.jpg"):
            logo_file = discord.File("fierylogo.jpg", filename="logo.png")
            embed.set_thumbnail(url="attachment://logo.png")
            
        embed.add_field(name="🏛️ ARENA RECORD", value=f"**Battles:** {total_fights}\n**Conquests:** {total_wins}\n**Valor Ratio:** {ratio:.1f}%", inline=True)
        embed.add_field(name="🔥 CURRENT STATUS", value=f"**Glory Streak:** {g_data.get('streak', 0)}\n**Imperial Rank:** Gladiator", inline=True)
        
        # Victims Logic
        victims = g_data.get("victims", {})
        if victims:
            v_sorted = sorted(victims.items(), key=lambda x: x[1], reverse=True)[:3]
            v_text = ""
            for vid, count in v_sorted:
                v_user = self.bot.get_user(int(vid))
                v_name = v_user.display_name if v_user else f"Fallen_{vid}"
                v_text += f"• **{v_name}**: {count} executions\n"
            embed.add_field(name="💀 TOP VICTIMS", value=v_text, inline=False)

        embed.set_footer(text=f"Gladiator ID: {tid}", icon_url=target.display_avatar.url)
        
        if logo_file:
            await ctx.send(file=logo_file, embed=embed)
        else:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DungeonFight(bot))
