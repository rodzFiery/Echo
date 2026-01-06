import discord
from discord.ext import commands
import sqlite3
import os
import random
import __main__
from datetime import datetime, timezone

class Bank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Database Setup - Using Railway Volume for persistence
        db_path = "/app/data/economy.db" if os.path.exists("/app/data") else "economy.db"
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # TABLE SCHEMA:
        # sparks: The primary currency
        # echo_xp: The experience points
        # echo_level: The user's current level
        # class_type: The user's chosen Echo Class
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                              (user_id INTEGER PRIMARY KEY, 
                               sparks INTEGER DEFAULT 100, 
                               echo_xp INTEGER DEFAULT 0, 
                               echo_level INTEGER DEFAULT 1,
                               class_type TEXT DEFAULT 'None')''')
        self.conn.commit()

        # Scenarios for immersion
        self.work_scenarios = [
            "You spent the morning stabilizing the Echo-Chamber.",
            "You helped a traveler navigate the Spark-Fields.",
            "You performed maintenance on the Sanctuary data-nodes.",
            "You spent hours polishing raw crystals for the market.",
            "You assisted an Elder in documenting Echo-History."
        ]
        self.job_scenarios = [
            "You completed a high-risk security contract for the Spark-Vault.",
            "You successfully recalibrated the main Sanctuary Echo-Core.",
            "You led an expedition deep into the Uncharted Caverns.",
            "You negotiated a massive trade deal between Sanctuary factions.",
            "You engineered a new power grid using pure Echo-Energy."
        ]

    def check_premium(self, guild_id):
        # Access global PREMIUM_GUILDS from main.py
        now = datetime.now(timezone.utc).timestamp()
        guild_id_str = str(guild_id)
        premium_data = getattr(__main__, 'PREMIUM_GUILDS', {})
        guild_mods = premium_data.get(guild_id_str, {})
        expiry = guild_mods.get('bank', 0)
        return expiry > now

    async def open_account(self, user_id):
        """Ensures the user exists in the economy engine database."""
        self.cursor.execute("SELECT sparks FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        if result is None:
            self.cursor.execute("INSERT INTO users (user_id, sparks, echo_xp, echo_level, class_type) VALUES (?, ?, ?, ?, ?)", 
                               (user_id, 100, 0, 1, 'None'))
            self.conn.commit()
            return True
        return False

    # --- INTERNAL ENGINE METHODS (To be called by other Cogs) ---

    async def update_sparks(self, user_id, amount):
        """Adds or removes Sparks. Amount can be positive or negative."""
        await self.open_account(user_id)
        self.cursor.execute("UPDATE users SET sparks = sparks + ? WHERE user_id = ?", (amount, user_id))
        self.conn.commit()

    async def update_echo_xp(self, user_id, amount):
        """Adds Echo XP and handles automatic leveling."""
        await self.open_account(user_id)
        self.cursor.execute("SELECT echo_xp, echo_level FROM users WHERE user_id = ?", (user_id,))
        xp, lvl = self.cursor.fetchone()
        
        new_xp = xp + amount
        # Leveling formula: Next Level = Level * 500 XP
        xp_needed = lvl * 500
        
        leveled_up = False
        while new_xp >= xp_needed:
            new_xp -= xp_needed
            lvl += 1
            leveled_up = True
            xp_needed = lvl * 500
            
        self.cursor.execute("UPDATE users SET echo_xp = ?, echo_level = ? WHERE user_id = ?", 
                           (new_xp, lvl, user_id))
        self.conn.commit()
        return leveled_up, lvl

    async def get_user_data(self, user_id):
        """Fetches all engine data for a specific user."""
        await self.open_account(user_id)
        self.cursor.execute("SELECT sparks, echo_xp, echo_level, class_type FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    # --- USER COMMANDS ---

    @commands.command(name="setclass")
    async def setclass(self, ctx, choice: str = None):
        """Choose your Class (Dominant, Submissive, Switch, Exhibitionist)"""
        await self.open_account(ctx.author.id)
        classes = {
            "dominant": "Dominant", 
            "submissive": "Submissive", 
            "switch": "Switch", 
            "exhibitionist": "Exhibitionist"
        }
        
        if choice is None or choice.lower() not in classes:
            embed = discord.Embed(title="💠 Choose Your Echo Archetype", color=0x00fbff)
            embed.description = (
                "**Dominant**: +20% Echo XP Bonus\n"
                "**Submissive**: +20% Sparks Bonus\n"
                "**Switch**: +10% Sparks & XP Bonus\n"
                "**Exhibitionist**: 15% Faster Cooldowns"
            )
            embed.set_footer(text="Use !setclass <name>")
            return await ctx.send(embed=embed)

        self.cursor.execute("UPDATE users SET class_type = ? WHERE user_id = ?", (classes[choice.lower()], ctx.author.id))
        self.conn.commit()
        await ctx.send(f"✨ Your soul has harmonized with the **{classes[choice.lower()]}** archetype!")

    @commands.command(name="profile", aliases=["stats", "sparks"])
    async def profile(self, ctx, member: discord.Member = None):
        """Displays the user's current Sparks and Echo Experience."""
        if not self.check_premium(ctx.guild.id):
            embed = discord.Embed(title="🔒 ENGINE LOCKED", color=0xff0000)
            embed.description = "The **ECONOMY ENGINE** is not active. An administrator must use `!premium` to unlock."
            return await ctx.send(embed=embed)

        member = member or ctx.author
        sparks, xp, lvl, class_type = await self.get_user_data(member.id)
        xp_needed = lvl * 500

        embed = discord.Embed(title=f"✨ {member.display_name}'s Profile", color=0x00fbff)
        embed.add_field(name="🛡️ Archetype", value=f"**{class_type}**", inline=False)
        embed.add_field(name="⚡ Sparks", value=f"**{sparks:,}**", inline=True)
        embed.add_field(name="💠 Echo Level", value=f"Level **{lvl}**", inline=True)
        
        # Visual Progress Bar for Echo XP
        progress = int((xp / xp_needed) * 10)
        bar = "▰" * progress + "▱" * (10 - progress)
        embed.add_field(name="📊 Echo Experience", value=f"{bar} ({xp}/{xp_needed} XP)", inline=False)
        
        if os.path.exists("fierylogo.jpg"):
            file = discord.File("fierylogo.jpg", filename="fierylogo.jpg")
            embed.set_thumbnail(url="attachment://fierylogo.jpg")
            await ctx.send(file=file, embed=embed)
        else:
            embed.set_thumbnail(url=member.display_avatar.url)
            await ctx.send(embed=embed)

    @commands.command(name="work")
    async def work(self, ctx):
        """Earn Sparks and XP through minor tasks (3h CD)"""
        if not self.check_premium(ctx.guild.id):
            return await ctx.send("🔒 Unlock the **BANK** module to use the `work` command.")
        
        # Cooldown Logic with Exhibitionist Bonus
        data = await self.get_user_data(ctx.author.id)
        class_type = data[3]
        
        # Manual Cooldown Check
        bucket = self.work._buckets.get_bucket(ctx)
        retry_after = bucket.update_rate_limit()
        
        # Apply Exhibitionist 15% reduction to the retry display if on cooldown
        if retry_after:
            if class_type == "Exhibitionist":
                retry_after *= 0.85
            minutes, seconds = divmod(retry_after, 60)
            return await ctx.send(f"⏳ Patience! You can earn more in **{int(minutes)}m {int(seconds)}s**.")

        sp_gain = random.randint(100, 3500)
        xp_gain = 1000
        
        # Apply Class Bonuses
        if class_type == "Dominant": xp_gain = int(xp_gain * 1.2)
        elif class_type == "Submissive": sp_gain = int(sp_gain * 1.2)
        elif class_type == "Switch":
            xp_gain = int(xp_gain * 1.1)
            sp_gain = int(sp_gain * 1.1)
        
        await self.update_sparks(ctx.author.id, sp_gain)
        lvl_up, new_lvl = await self.update_echo_xp(ctx.author.id, xp_gain)
        
        embed = discord.Embed(title="⚒️ Work Complete", description=random.choice(self.work_scenarios), color=0x2ecc71)
        embed.add_field(name="Rewards", value=f"⚡ **{sp_gain}** Sparks\n💠 **{xp_gain}** Echo XP")
        if lvl_up: embed.add_field(name="✨ Level Up!", value=f"You reached Level **{new_lvl}**!", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="job")
    async def job(self, ctx):
        """Earn Sparks and XP through high-tier contracts (5h CD)"""
        if not self.check_premium(ctx.guild.id):
            return await ctx.send("🔒 Unlock the **BANK** module to use the `job` command.")
        
        data = await self.get_user_data(ctx.author.id)
        class_type = data[3]
        
        bucket = self.job._buckets.get_bucket(ctx)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            if class_type == "Exhibitionist":
                retry_after *= 0.85
            minutes, seconds = divmod(retry_after, 60)
            return await ctx.send(f"⏳ Patience! You can earn more in **{int(minutes)}m {int(seconds)}s**.")

        sp_gain = random.randint(500, 5000)
        xp_gain = 2000
        
        # Apply Class Bonuses
        if class_type == "Dominant": xp_gain = int(xp_gain * 1.2)
        elif class_type == "Submissive": sp_gain = int(sp_gain * 1.2)
        elif class_type == "Switch":
            xp_gain = int(xp_gain * 1.1)
            sp_gain = int(sp_gain * 1.1)
        
        await self.update_sparks(ctx.author.id, sp_gain)
        lvl_up, new_lvl = await self.update_echo_xp(ctx.author.id, xp_gain)
        
        embed = discord.Embed(title="💼 Job Finished", description=random.choice(self.job_scenarios), color=0x3498db)
        embed.add_field(name="Rewards", value=f"⚡ **{sp_gain}** Sparks\n💠 **{xp_gain}** Echo XP")
        if lvl_up: embed.add_field(name="✨ Level Up!", value=f"You reached Level **{new_lvl}**!", inline=False)
        await ctx.send(embed=embed)

    @work.error
    @job.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            await ctx.send(f"⏳ Patience! You can earn more in **{int(hours)}h {int(minutes)}m {int(seconds)}s**.")

async def setup(bot):
    await bot.add_cog(Bank(bot))
