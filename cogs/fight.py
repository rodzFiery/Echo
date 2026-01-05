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
        if os.path.exists(self.stats_file):
            with open(self.stats_file, "r") as f:
                self.stats = json.load(f)
        else:
            self.stats = {"global": {}, "servers": {}}

    def _save_stats(self):
        with open(self.stats_file, "w") as f:
            json.dump(self.stats, f, indent=4)

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
        if not is_premium:
            # Standard ASCII Bar
            filled = int((hp / max_hp) * 10)
            return f"[{'█' * filled}{'░' * (10 - filled)}] {hp}/{max_hp}"
        
        # Premium Gradient Visual logic
        pct = (hp / max_hp) * 100
        if pct > 75: bar_emoji = "🟩🟩🟩🟩"
        elif pct > 50: bar_emoji = "🟩🟩🟨🟨"
        elif pct > 25: bar_emoji = "🟨🟨🟧🟧"
        else: bar_emoji = "🟧🟧🟥🟥"
        
        return f"{bar_emoji} **{pct:.0f}%** ({hp} HP)"

    def get_funny_msg(self, action_type):
        msgs = {
            "strike": [
                "swung a wet noodle at",
                "delivered a legendary slap to",
                "poked the eye of",
                "threw a heavy dictionary at",
                "used a gamer move on",
                "challenged the physics of the universe hitting",
                "sent a strongly worded email to the face of",
                "tried to delete the existence of",
                "performed a professional wrestling dropkick on",
                "threw a spoiled slice of pizza at",
                "whispered an embarrassing secret to distract",
                "bonked the head of",
                "accidentally sneezed too hard on",
                "used a selfie stick as a spear against",
                "threw a handful of glitter into the eyes of",
                "attempted a 360-no-scope slap on",
                "lightly tapped the shoulder of",
                "summoned a tiny, angry pigeon to peck",
                "dropped a massive piano (cartoon style) on",
                "hit a home run using the head of"
            ],
            "heal": [
                "ate a suspicious mushroom.",
                "drank a glowing potion that tastes like blueberry.",
                "took a quick nap mid-battle.",
                "used a band-aid on a broken heart.",
                "screamed 'I REFUSE TO DIE' and felt better.",
                "found a half-eaten sandwich on the floor.",
                "rubbed some dirt on the wound.",
                "recalled a happy memory and gained life.",
                "drank some spicy lava juice.",
                "patched themselves up with duct tape.",
                "received a magical high-five from a ghost.",
                "consumed an entire wheel of cheese instantly.",
                "hugged a nearby cactus for some reason.",
                "re-read the instructions of the fight.",
                "activated 'Main Character' plot armor.",
                "took a sip of a very expensive energy drink.",
                "prayed to the gods of the Echo.",
                "remembered they left the stove on and panicked into health.",
                "did a quick yoga pose to realign their soul.",
                "smelled a very refreshing lemon."
            ]
        }
        return random.choice(msgs[action_type])

    # --- IMAGE ENGINE FOR ARENA VISUALS ---
    async def create_arena_visual(self, u1_url, u2_url):
        try:
            # maximized realistic arena canvas
            canvas = Image.new("RGBA", (1200, 600), (20, 20, 20, 255))
            draw = ImageDraw.Draw(canvas)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1, p2 = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())
            
            av_size = 450 # Max size for avatars
            av1_raw = Image.open(p1).convert("RGBA").resize((av_size, av_size))
            av2_raw = Image.open(p2).convert("RGBA").resize((av_size, av_size))

            # Borderless circular clipping
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, av_size, av_size), fill=255)
            
            av1 = ImageOps.fit(av1_raw, mask.size, centering=(0.5, 0.5))
            av1.putalpha(mask)
            av2 = ImageOps.fit(av2_raw, mask.size, centering=(0.5, 0.5))
            av2.putalpha(mask)

            # Paste Avatars
            canvas.paste(av1, (50, 75), av1)
            canvas.paste(av2, (700, 75), av2)

            # Draw Central Crossed Axes Symbol
            draw.line([530, 230, 670, 370], fill=(200, 200, 200, 255), width=15) # Axis 1
            draw.line([670, 230, 530, 370], fill=(200, 200, 200, 255), width=15) # Axis 2
            
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except:
            return None

    # --- WINNER CARD ENGINE ---
    async def create_winner_card(self, winner_url, name, wins, total_fights, streak):
        try:
            # Base card setup
            card = Image.new("RGBA", (1000, 500), (15, 15, 15, 255))
            draw = ImageDraw.Draw(card)
            
            # Load fierylogo.jpg if exists
            if os.path.exists("fierylogo.jpg"):
                logo = Image.open("fierylogo.jpg").convert("RGBA").resize((1000, 500))
                overlay = Image.new("RGBA", (1000, 500), (0, 0, 0, 160))
                card.paste(logo, (0, 0))
                card.paste(overlay, (0, 0), overlay)

            # Load Winner Avatar
            async with aiohttp.ClientSession() as session:
                async with session.get(winner_url) as r:
                    av_data = io.BytesIO(await r.read())
            
            av_size = 300
            av = Image.open(av_data).convert("RGBA").resize((av_size, av_size))
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, av_size, av_size), fill=255)
            av.putalpha(mask)
            
            # Draw Avatar and Gold Border
            card.paste(av, (50, 100), av)
            draw.ellipse((45, 95, 355, 405), outline=(255, 215, 0), width=10)

            # Text Rendering
            draw.text((400, 80), "ARENA CHAMPION", fill=(255, 69, 0))
            draw.text((400, 130), name.upper(), fill=(255, 255, 255))
            
            draw.text((400, 220), f"TOTAL WINS: {wins}", fill=(255, 215, 0))
            draw.text((400, 270), f"CURRENT STREAK: {streak} 🔥", fill=(255, 100, 0))
            draw.text((400, 320), f"TOTAL FIGHTS: {total_fights}", fill=(200, 200, 200))
            
            acc = (wins / total_fights) * 100 if total_fights > 0 else 0
            draw.text((400, 370), f"WIN RATE: {acc:.1f}%", fill=(0, 255, 127))

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
            return await ctx.send("💢 You can't fight yourself. Stop punching the air.")

        if member.bot:
            return await ctx.send("🤖 Bots don't feel pain. You'd lose instantly to the machine.")

        # --- SUBSCRIPTION CHECK ---
        guild_id = str(ctx.guild.id)
        is_premium = False
        if guild_id in __main__.PREMIUM_GUILDS:
            guild_data = __main__.PREMIUM_GUILDS[guild_id]
            if isinstance(guild_data, dict):
                expiry = guild_data.get(self.module_name)
                if expiry and expiry > datetime.now(timezone.utc).timestamp():
                    is_premium = True

        # Initial Stats
        p1 = {"user": ctx.author, "hp": 100, "max": 100, "luck": 1.0}
        p2 = {"user": member, "hp": 100, "max": 100, "luck": 1.0}
        turn = p1
        other = p2
        battle_log = "🌋 **THE ARENA RADIATES HEAT!** The crowd is waiting for the first drop of blood."

        embed = discord.Embed(title="⚔️ ECHO ARENA: THE DUEL BEGINS", color=0xff4500)
        embed.description = f"🔥 **{p1['user'].mention}** HAS CHALLENGED **{p2['user'].mention}**\n\n*\"In the echo of battle, only one will stand!\"*"
        
        # Thumbnail Logic
        logo_file = None
        if os.path.exists("fierylogo.jpg"):
            logo_file = discord.File("fierylogo.jpg", filename="logo.png")
            embed.set_thumbnail(url="attachment://logo.png")

        # Arena Image Generation
        arena_img = await self.create_arena_visual(p1['user'].display_avatar.url, p2['user'].display_avatar.url)
        arena_file = discord.File(arena_img, filename="arena.png")
        embed.set_image(url="attachment://arena.png")
        
        files = [arena_file]
        if logo_file: files.append(logo_file)
        
        main_msg = await ctx.send(files=files, embed=embed)

        # --- AUTOMATED COMBAT LOOP ---
        while p1["hp"] > 0 and p2["hp"] > 0:
            await asyncio.sleep(2.5)
            
            action = random.choices(["strike", "heal"], weights=[70, 30])[0]
            
            if action == "strike":
                dmg = int(random.randint(12, 28) * turn["luck"])
                other["hp"] = max(0, other["hp"] - dmg)
                battle_log = f"💥 **{turn['user'].display_name}** {self.get_funny_msg('strike')} **{other['user'].display_name}** for **{dmg} damage!**"
            else:
                amt = random.randint(10, 22)
                turn["hp"] = min(turn["max"], turn["hp"] + amt)
                battle_log = f"🧪 **{turn['user'].display_name}** {self.get_funny_msg('heal')} (+{amt} HP)"

            embed = discord.Embed(title="🌋 ECHO ARENA: BATTLE RAGING", color=0xff4500)
            embed.set_image(url="attachment://arena.png")
            if os.path.exists("fierylogo.jpg"):
                embed.set_thumbnail(url="attachment://logo.png")
            
            p1_status = f"{self.get_health_bar(p1['hp'], p1['max'], is_premium)}"
            if p1['luck'] > 1.0: p1_status += " ✨ **BLESSED**"
            p2_status = f"{self.get_health_bar(p2['hp'], p2['max'], is_premium)}"
            if p2['luck'] > 1.0: p2_status += " ✨ **BLESSED**"

            embed.add_field(name=f"🛡️ {p1['user'].display_name}", value=p1_status, inline=True)
            embed.add_field(name=f"🛡️ {p2['user'].display_name}", value=p2_status, inline=True)
            embed.add_field(name="📜 COMBAT LOG", value=f"> *{battle_log}*", inline=False)
            embed.set_footer(text=f"🔥 Turn: {turn['user'].display_name.upper()} | CRUSH THEM!")

            view = discord.ui.View(timeout=1)
            cheer_btn = discord.ui.Button(label="CHEER!", style=discord.ButtonStyle.danger, emoji="🙌")
            
            async def cheer_callback(interaction):
                if interaction.user.id in [p1["user"].id, p2["user"].id]:
                    return await interaction.response.send_message("💢 You're too busy fighting! Focus!", ephemeral=True)
                turn["luck"] += 0.05
                await interaction.response.send_message(f"📣 **{interaction.user.display_name}** roars! **{turn['user'].display_name}** is fueled!", ephemeral=False)

            cheer_btn.callback = cheer_callback
            view.add_item(cheer_btn)

            await main_msg.edit(embed=embed, view=view)

            if other["hp"] <= 0:
                break

            turn, other = other, turn

        # Winner Announcement & Stats Update
        winner = turn if turn["hp"] > 0 else other
        loser = other if turn["hp"] > 0 else turn
        self._update_winner(ctx.guild.id, winner["user"].id, loser["user"].id)

        # Generate Winner Card with Streak
        win_data = self.stats["global"].get(str(winner["user"].id), {"wins": 0, "fights": 0, "streak": 0})
        win_card_buf = await self.create_winner_card(
            winner["user"].display_avatar.url, 
            winner["user"].display_name, 
            win_data["wins"], 
            win_data["fights"],
            win_data["streak"]
        )

        win_emb = discord.Embed(title="🏆 THE ECHO CHAMPION EMERGES", color=0x00ff00)
        win_emb.description = f"🎊 **{winner['user'].display_name.upper()}** HAS CLAIMED THE THRONE!"
        
        if win_card_buf:
            win_file = discord.File(win_card_buf, filename="winner_card.png")
            win_emb.set_image(url="attachment://winner_card.png")
            await ctx.send(file=win_file, embed=win_emb)
        else:
            await ctx.send(embed=win_emb)

    @commands.command(name="fightrank")
    async def fightrank(self, ctx, user: discord.Member = None):
        """Displays combat ranking and victim stats. Usage: !fightrank [@user]"""
        target = user or ctx.author
        tid = str(target.id)
        gid = str(ctx.guild.id)

        g_data = self.stats["global"]
        g_sorted = sorted(g_data.items(), key=lambda x: x[1]["wins"], reverse=True)
        g_pos = next((i for i, (uid, _) in enumerate(g_sorted, 1) if uid == tid), "N/A")
        g_wins = g_data.get(tid, {}).get("wins", 0)
        g_streak = g_data.get(tid, {}).get("streak", 0)

        l_data = self.stats["servers"].get(gid, {})
        l_sorted = sorted(l_data.items(), key=lambda x: x[1]["wins"], reverse=True)
        l_pos = next((i for i, (uid, _) in enumerate(l_sorted, 1) if uid == tid), "N/A")
        l_wins = l_data.get(tid, {}).get("wins", 0)

        embed = discord.Embed(title=f"🛡️ COMBATANT RANK: {target.display_name.upper()}", color=0xff4500)
        
        if os.path.exists("fierylogo.jpg"):
            file = discord.File("fierylogo.jpg", filename="rank_logo.png")
            embed.set_thumbnail(url="attachment://rank_logo.png")
        
        embed.add_field(name="🌍 GLOBAL STANDING", value=f"**Rank:** #{g_pos}\n**Total Wins:** {g_wins}\n**Streak:** {g_streak} 🔥", inline=True)
        embed.add_field(name="🏰 LOCAL STANDING", value=f"**Rank:** #{l_pos}\n**Server Wins:** {l_wins}", inline=True)

        victims = g_data.get(tid, {}).get("victims", {})
        if victims:
            v_sorted = sorted(victims.items(), key=lambda x: x[1], reverse=True)[:5]
            v_text = ""
            for vid, count in v_sorted:
                v_user = self.bot.get_user(int(vid))
                v_name = v_user.display_name if v_user else f"Fallen_{vid}"
                v_text += f"• **{v_name}**: {count} kills\n"
            embed.add_field(name="💀 TOP GLOBAL VICTIMS", value=v_text, inline=False)
        else:
            embed.add_field(name="💀 TOP GLOBAL VICTIMS", value="No victims recorded yet.", inline=False)

        embed.set_footer(text=f"Server ID: {gid} | Keep fighting to climb the ranks!")
        
        if os.path.exists("fierylogo.jpg"):
            await ctx.send(file=file, embed=embed)
        else:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DungeonFight(bot))
