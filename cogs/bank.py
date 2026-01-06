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

        # Scenarios for immersion (Updated with 3 new Work and 3 new Job scenarios)
        self.work_scenarios = [
            "You spent the morning stabilizing the Echo-Chamber.",
            "You helped a traveler navigate the Spark-Fields.",
            "You performed maintenance on the Sanctuary data-nodes.",
            "You spent hours polishing raw crystals for the market.",
            "You assisted an Elder in documenting Echo-History.",
            "You spent the day harvesting wild Spark-Berries for the locals.",
            "You spent hours scrubbing the graffiti off the Sanctuary walls.",
            "You worked a shift as a temporary guide for the Echo-Catacombs."
        ]
        self.job_scenarios = [
            "You completed a high-risk security contract for the Spark-Vault.",
            "You successfully recalibrated the main Sanctuary Echo-Core.",
            "You led an expedition deep into the Uncharted Caverns.",
            "You negotiated a massive trade deal between Sanctuary factions.",
            "You engineered a new power grid using pure Echo-Energy.",
            "You successfully infiltrated a rival faction's Echo-Archive.",
            "You neutralized a dangerous rogue-spirit haunting the Spark-Core.",
            "You designed a revolutionary Echo-Interface for the High Council."
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
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def work(self, ctx):
        """Earn Sparks and XP through minor tasks (3h CD)"""
        if not self.check_premium(ctx.guild.id):
            self.work.reset_cooldown(ctx)
            return await ctx.send("🔒 Unlock the **BANK** module to use the `work` command.")
        
        # Cooldown Logic with Exhibitionist Bonus
        data = await self.get_user_data(ctx.author.id)
        class_type = data[3]
        
        # Manual Cooldown Check (Note: Decorator handles standard, logic below handles rewards)
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
        
        # Fetch NEW balance for the response
        updated_data = await self.get_user_data(ctx.author.id)
        new_balance = updated_data[0]
        
        embed = discord.Embed(title="⚒️ Work Complete", description=random.choice(self.work_scenarios), color=0x2ecc71)
        embed.add_field(name="Rewards", value=f"⚡ **+{sp_gain}** Sparks\n💠 **+{xp_gain}** Echo XP")
        embed.add_field(name="💰 New Balance", value=f"**{new_balance:,}** Sparks", inline=False)
        if lvl_up: embed.add_field(name="✨ Level Up!", value=f"You reached Level **{new_lvl}**!", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="job")
    @commands.cooldown(1, 18000, commands.BucketType.user)
    async def job(self, ctx):
        """Earn Sparks and XP through high-tier contracts (5h CD)"""
        if not self.check_premium(ctx.guild.id):
            self.job.reset_cooldown(ctx)
            return await ctx.send("🔒 Unlock the **BANK** module to use the `job` command.")
        
        data = await self.get_user_data(ctx.author.id)
        class_type = data[3]

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

        # Fetch NEW balance for the response
        updated_data = await self.get_user_data(ctx.author.id)
        new_balance = updated_data[0]
        
        embed = discord.Embed(title="💼 Job Finished", description=random.choice(self.job_scenarios), color=0x3498db)
        embed.add_field(name="Rewards", value=f"⚡ **+{sp_gain}** Sparks\n💠 **+{xp_gain}** Echo XP")
        embed.add_field(name="💰 New Balance", value=f"**{new_balance:,}** Sparks", inline=False)
        if lvl_up: embed.add_field(name="✨ Level Up!", value=f"You reached Level **{new_lvl}**!", inline=False)
        await ctx.send(embed=embed)

    # --- EXPANDED COMMANDS (Categorized as Work or Job) ---

    @commands.command(name="clean")
    async def clean(self, ctx):
        """Work category: Clean the Sanctuary floors."""
        self.work.reset_cooldown(ctx) # Shared cooldown with work
        await ctx.invoke(self.bot.get_command('work'))

    @commands.command(name="beg")
    async def beg(self, ctx):
        """Work category: Beg for Sparks in the Echo-Plaza."""
        self.work.reset_cooldown(ctx)
        await ctx.invoke(self.bot.get_command('work'))

    @commands.command(name="slut")
    async def slut(self, ctx):
        """Work category: Sell your Echo-energy on the street."""
        self.work.reset_cooldown(ctx)
        await ctx.invoke(self.bot.get_command('work'))

    @commands.command(name="farm")
    async def farm(self, ctx):
        """Work category: Harvest resources from the Spark-Fields."""
        self.work.reset_cooldown(ctx)
        await ctx.invoke(self.bot.get_command('work'))

    @commands.command(name="cook")
    async def cook(self, ctx):
        """Work category: Prepare Echo-infused meals for travelers."""
        self.work.reset_cooldown(ctx)
        await ctx.invoke(self.bot.get_command('work'))

    @commands.command(name="mine")
    async def mine(self, ctx):
        """Work category: Extract raw crystals from the Sanctuary mines."""
        self.work.reset_cooldown(ctx)
        await ctx.invoke(self.bot.get_command('work'))

    @commands.command(name="crime")
    async def crime(self, ctx):
        """Job category: Attempt a high-stakes Echo-heist."""
        self.job.reset_cooldown(ctx) # Shared cooldown with job
        await ctx.invoke(self.bot.get_command('job'))

    @commands.command(name="pimp")
    async def pimp(self, ctx):
        """Job category: Manage a ring of Echo-energy sellers."""
        self.job.reset_cooldown(ctx)
        await ctx.invoke(self.bot.get_command('job'))

    @commands.command(name="hack")
    async def hack(self, ctx):
        """Job category: Breach a high-security Sanctuary data-node."""
        self.job.reset_cooldown(ctx)
        await ctx.invoke(self.bot.get_command('job'))

    @commands.command(name="assassinate")
    async def assassinate(self, ctx):
        """Job category: Take down a rogue entity threatening the Echo-Chamber."""
        self.job.reset_cooldown(ctx)
        await ctx.invoke(self.bot.get_command('job'))

    @commands.command(name="smuggle")
    async def smuggle(self, ctx):
        """Job category: Transport illegal Echo-crystals past Sanctuary guards."""
        self.job.reset_cooldown(ctx)
        await ctx.invoke(self.bot.get_command('job'))

    @work.error
    @job.error
    @clean.error
    @beg.error
    @slut.error
    @farm.error
    @cook.error
    @mine.error
    @crime.error
    @pimp.error
    @hack.error
    @assassinate.error
    @smuggle.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            data = await self.get_user_data(ctx.author.id)
            class_type = data[3]
            retry_after = error.retry_after
            
            # Apply Exhibitionist 15% reduction to the cooldown message
            if class_type == "Exhibitionist":
                retry_after *= 0.85

            minutes, seconds = divmod(retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            await ctx.send(f"⏳ Patience! You can earn more in **{int(hours)}h {int(minutes)}m {int(seconds)}s**.")

async def setup(bot):
    await bot.add_cog(Bank(bot))
