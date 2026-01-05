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
        if pct >= 55: bar_color = "🟢"
        elif pct >= 25: bar_color = "🟡"
        else: bar_color = "🔴"
        
        # Dynamic Segmented Bar (10 segments)
        filled = max(0, min(10, int(pct / 10)))
        empty = 10 - filled
        bar_str = "▬" * filled + "  " + "▬" * empty
        
        return f"{bar_color} **{bar_str}** {pct:.0f}% ({hp}/{max_hp} HP)"

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
                "ate a suspicious mushroom.", "drank a glowing potion that tastes like blueberry.", "took a quick nap mid-battle.",
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
            # Roman Empire Cinematic Background (Base canvas 1200x600)
            if os.path.exists("fight.jpg"):
                canvas = Image.open("fight.jpg").convert("RGBA").resize((1200, 600))
            else:
                canvas = Image.new("RGBA", (1200, 600), (40, 0, 0, 255))
            
            draw = ImageDraw.Draw(canvas)
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1_data, p2_data = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())
            
            av_size = 450 
            av1_raw = Image.open(p1_data).convert("RGBA").resize((av_size, av_size))
            av2_raw = Image.open(p2_data).convert("RGBA").resize((av_size, av_size))

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

            canvas.paste(av1, (50, 60), av1)
            canvas.paste(av2, (700, 60), av2)
            canvas = Image.alpha_composite(canvas, lighting)
            draw = ImageDraw.Draw(canvas)

            # Status Icons (Trophy/RIP) Logic
            if p2_hp <= 0:
                draw.text((275, 400), "🏆", font=None, size=80, anchor="mm")
                draw.text((925, 400), "🪦", font=None, size=80, anchor="mm")
            elif p1_hp <= 0:
                draw.text((275, 400), "🪦", font=None, size=80, anchor="mm")
                draw.text((925, 400), "🏆", font=None, size=80, anchor="mm")

            draw.text((600, 80), "ARENA FIGHT!", fill=(255, 255, 255), anchor="mm", stroke_width=2, stroke_fill=(0,0,0))
            draw.text((600, 280), "VS", fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(0,0,0))
            
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except:
            return None

    # --- WINNER CARD ENGINE ---
    async def create_winner_card(self, winner_url, name, wins, total_fights, streak):
        try:
            card = Image.new("RGBA", (1000, 500), (10, 10, 10, 255))
            draw = ImageDraw.Draw(card)
            if os.path.exists("fierylogo.jpg"):
                logo = Image.open("fierylogo.jpg").convert("RGBA").resize((1000, 500))
                card.paste(logo, (0, 0))

            async with aiohttp.ClientSession() as session:
                async with session.get(winner_url) as r:
                    av_data = io.BytesIO(await r.read())
            
            av = Image.open(av_data).convert("RGBA").resize((320, 320))
            mask = Image.new("L", (320, 320), 0)
            ImageDraw.Draw(mask).ellipse((10, 10, 310, 310), fill=255)
            av.putalpha(mask)
            
            card.paste(av, (60, 90), av)
            draw.text((430, 70), "LEGIONNAIRE VICTOR", fill=(255, 215, 0))
            draw.text((430, 120), name.upper(), fill=(255, 255, 255))
            draw.text((430, 220), f"CONQUESTS: {wins}", fill=(212, 175, 55))
            draw.text((430, 275), f"BLOOD STREAK: {streak} 🔥", fill=(255, 69, 0))
            
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
        battle_log = "🏛️ **THE GATES OPEN!** The crowd roars as the fight begins."

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
                battle_log = f"🗡️ **{turn['user'].display_name}** {self.get_funny_msg('strike')} **{other['user'].display_name}**, dealing **-{dmg}** damage!"
                emb_color = 0xFF4500 if dmg > 20 else 0x8B0000
            else:
                amt = random.randint(10, 22)
                turn["hp"] = min(turn["max"], turn["hp"] + amt)
                battle_log = f"🏺 **{turn['user'].display_name}** {self.get_funny_msg('heal')} (+{amt} HP)"
                emb_color = 0x50C878

            arena_img = await self.create_arena_visual(p1['user'].display_avatar.url, p2['user'].display_avatar.url, p1['hp'], p2['hp'])
            arena_file = discord.File(arena_img, filename="arena.png")

            embed = discord.Embed(title=f"🏆 Victory! {turn['user'].display_name} was victorious!" if other["hp"] <= 0 else "🏟️ THE COLOSSEUM RADIATES GLORY", color=emb_color)
            embed.set_image(url="attachment://arena.png")
            embed.add_field(name=f"🔵 {p1['user'].display_name}", value=self.get_health_bar(p1['hp'], p1['max'], is_premium), inline=False)
            embed.add_field(name=f"🔴 {p2['user'].display_name}", value=self.get_health_bar(p2['hp'], p2['max'], is_premium), inline=False)
            embed.add_field(name="📜 BATTLE LOG", value=f"> *{battle_log}*", inline=False)
            embed.set_footer(text=f"🚩 Turn: {turn['user'].display_name.upper()} | Glory to the Echo!")

            await main_msg.edit(attachments=[arena_file], embed=embed)
            if other["hp"] <= 0: break
            turn, other = other, turn

        winner = turn if turn["hp"] > 0 else other
        loser = other if turn["hp"] > 0 else turn
        self._update_winner(ctx.guild.id, winner["user"].id, loser["user"].id)

        win_data = self.stats["global"].get(str(winner["user"].id), {"wins": 0, "fights": 0, "streak": 0})
        win_card_buf = await self.create_winner_card(winner["user"].display_avatar.url, winner["user"].display_name, win_data["wins"], win_data["fights"], win_data["streak"])
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
