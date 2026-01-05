import discord
from discord.ext import commands
import random
import asyncio
import os
import io
import aiohttp
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageOps
import __main__

class DungeonFight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module_name = "fight"

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
                "used a gamer move on"
            ],
            "heal": [
                "ate a suspicious mushroom.",
                "drank a glowing potion that tastes like blueberry.",
                "took a quick nap mid-battle.",
                "used a band-aid on a broken heart.",
                "screamed 'I REFUSE TO DIE' and felt better."
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

    @commands.command(name="fight")
    async def fight(self, ctx, member: discord.Member = None):
        if member is None:
            return await ctx.send("❌ Mention someone to challenge them to a duel!")
        
        if member.id == ctx.author.id:
            return await ctx.send("You can't fight yourself. That's just called a workout.")

        if member.bot:
            return await ctx.send("Bots don't feel pain. You'd lose instantly.")

        # --- SUBSCRIPTION CHECK ---
        guild_id = str(ctx.guild.id)
        is_premium = False
        if guild_id in __main__.PREMIUM_GUILDS:
            guild_data = __main__.PREMIUM_GUILDS[guild_id]
            if isinstance(guild_data, dict):
                expiry = guild_data.get(self.module_name)
                if expiry and expiry > datetime.now(timezone.utc).timestamp():
                    is_premium = True

        # Initial Stats (Added Luck key)
        p1 = {"user": ctx.author, "hp": 100, "max": 100, "luck": 1.0}
        p2 = {"user": member, "hp": 100, "max": 100, "luck": 1.0}
        turn = p1
        other = p2
        battle_log = "The arena is silent... awaiting the first strike."

        embed = discord.Embed(title="⚔️ DUEL INITIATED", color=0xff4500)
        embed.description = f"{p1['user'].mention} vs {p2['user'].mention}\n\n*Fight for honor!*"
        
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

        # AUTOMATED TURN SYSTEM
        while p1["hp"] > 0 and p2["hp"] > 0:
            # Random balancing (70% strike, 30% heal)
            action = random.choices(["strike", "heal"], weights=[70, 30])[0]
            
            if action == "strike":
                dmg = int(random.randint(12, 28) * turn["luck"])
                other["hp"] = max(0, other["hp"] - dmg)
                battle_log = f"**{turn['user'].display_name}** {self.get_funny_msg('strike')} **{other['user'].display_name}** for **{dmg} damage!**"
            else:
                amt = random.randint(10, 22)
                turn["hp"] = min(turn["max"], turn["hp"] + amt)
                battle_log = f"**{turn['user'].display_name}** {self.get_funny_msg('heal')} (+{amt} HP)"

            # Refresh Embed
            embed = discord.Embed(title="⚔️ ARENA OF GLORY", color=0x2f3136)
            embed.set_image(url="attachment://arena.png")
            if os.path.exists("fierylogo.jpg"):
                embed.set_thumbnail(url="attachment://logo.png")
            
            p1_status = f"{self.get_health_bar(p1['hp'], p1['max'], is_premium)}"
            if p1['luck'] > 1.0: p1_status += " ✨ *LUCKY*"
            p2_status = f"{self.get_health_bar(p2['hp'], p2['max'], is_premium)}"
            if p2['luck'] > 1.0: p2_status += " ✨ *LUCKY*"

            embed.add_field(name=f"👤 {p1['user'].display_name}", value=p1_status, inline=True)
            embed.add_field(name=f"👤 {p2['user'].display_name}", value=p2_status, inline=True)
            embed.add_field(name="📜 Battle Logs", value=f"*{battle_log}*", inline=False)
            embed.set_footer(text=f"Round Active... | Attacking: {turn['user'].display_name}")

            # Spectator Cheering Button
            view = discord.ui.View(timeout=3)
            cheer_btn = discord.ui.Button(label="Cheering!", style=discord.ButtonStyle.secondary, emoji="🙌")
            
            async def cheer_callback(interaction):
                if interaction.user.id in [p1["user"].id, p2["user"].id]:
                    return await interaction.response.send_message("You're busy fighting!", ephemeral=True)
                turn["luck"] += 0.05
                await interaction.response.send_message(f"📣 {interaction.user.display_name} cheers for {turn['user'].display_name}!", ephemeral=False)

            cheer_btn.callback = cheer_callback
            view.add_item(cheer_btn)

            await main_msg.edit(embed=embed, view=view)

            if other["hp"] <= 0:
                break

            # Switch turns and delay for realism
            turn, other = other, turn
            await asyncio.sleep(2.5)

        # Winner Announcement
        winner = turn if turn["hp"] > 0 else other
        win_emb = discord.Embed(title="🏆 THE CHAMPION EMERGES", color=0x00ff00)
        win_emb.description = f"**{winner['user'].display_name}** stands victorious in the arena!\n\n*The crowd goes wild!*"
        win_emb.set_image(url="attachment://arena.png")
        
        if os.path.exists("fierylogo.jpg"):
            win_emb.set_thumbnail(url="attachment://logo.png")
        
        await ctx.send(embed=win_emb)

async def setup(bot):
    await bot.add_cog(DungeonFight(bot))
