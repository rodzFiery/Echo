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
        # Ensure directory exists to prevent silent loading failure
        db_dir = "/app/data"
        if os.path.exists(db_dir):
            db_path = os.path.join(db_dir, "economy.db")
        else:
            db_path = "economy.db"
            
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
        # Access global PREMIUM_GUILDS from main.py safely
        now = datetime.now(timezone.utc).timestamp()
        guild_id_str = str(guild_id)
        
        # Check if we are running in the Dev Server (ID from your main.py)
        if guild_id == 1457658274496118786:
            return True

        # Attempt to grab the latest data from the main module
        try:
            premium_data = getattr(__main__, 'PREMIUM_GUILDS', {})
            guild_mods = premium_data.get(guild_id_str, {})
            # Check specifically for the 'bank' module entry
            expiry = guild_mods.get('bank', 0)
            return expiry > now
        except Exception:
            return False

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

    # --- INTERNAL ENGINE METHODS ---

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

    # --- REWARD EXECUTION LOGIC ---

    async def execute_work(self, ctx):
        """Internal logic to process work rewards."""
        if not self.check_premium(ctx.guild.id):
            return await ctx.send("🔒 Unlock the **BANK** module to use this command.")

        data = await self.get_user_data(ctx.author.id)
        class_type = data[3]
        sp_gain = random.randint(100, 3500)
        xp_gain = 1000

        if class_type == "Dominant": xp_gain = int(xp_gain * 1.2)
        elif class_type == "Submissive": sp_gain = int(sp_gain * 1.2)
        elif class_type == "Switch":
            xp_gain = int(xp_gain * 1.1)
            sp_gain = int(sp_gain * 1.1)

        await self.update_sparks(ctx.author.id, sp_gain)
        lvl_up, new_lvl = await self.update_echo_xp(ctx.author.id, xp_gain)
        updated_data = await self.get_user_data(ctx.author.id)

        embed = discord.Embed(title="⚒️ Work Complete", description=random.choice(self.work_scenarios), color=0x2ecc71)
        embed.add_field(name="Rewards", value=f"⚡ **+{sp_gain}** Sparks\n💠 **+{xp_gain}** Echo XP")
        embed.add_field(name="💰 New Balance", value=f"**{updated_data[0]:,}** Sparks", inline=False)
        if lvl_up: embed.add_field(name="✨ Level Up!", value=f"You reached Level **{new_lvl}**!", inline=False)
        await ctx.send(embed=embed)

    async def execute_job(self, ctx):
        """Internal logic to process job rewards."""
        if not self.check_premium(ctx.guild.id):
            return await ctx.send("🔒 Unlock the **BANK** module to use this command.")

        data = await self.get_user_data(ctx.author.id)
        class_type = data[3]
        sp_gain = random.randint(500, 5000)
        xp_gain = 2000

        if class_type == "Dominant": xp_gain = int(xp_gain * 1.2)
        elif class_type == "Submissive": sp_gain = int(sp_gain * 1.2)
        elif class_type == "Switch":
            xp_gain = int(xp_gain * 1.1)
            sp_gain = int(sp_gain * 1.1)

        await self.update_sparks(ctx.author.id, sp_gain)
        lvl_up, new_lvl = await self.update_echo_xp(ctx.author.id, xp_gain)
        updated_data = await self.get_user_data(ctx.author.id)

        embed = discord.Embed(title="💼 Job Finished", description=random.choice(self.job_scenarios), color=0x3498db)
        embed.add_field(name="Rewards", value=f"⚡ **+{sp_gain}** Sparks\n💠 **+{xp_gain}** Echo XP")
        embed.add_field(name="💰 New Balance", value=f"**{updated_data[0]:,}** Sparks", inline=False)
        if lvl_up: embed.add_field(name="✨ Level Up!", value=f"You reached Level **{new_lvl}**!", inline=False)
        await ctx.send(embed=embed)

    # --- USER COMMANDS ---

    @commands.command(name="setclass")
    async def setclass(self, ctx, choice: str = None):
        """Choose your Class (Dominant, Submissive, Switch, Exhibitionist)"""
        await self.open_account(ctx.author.id)
        classes = {"dominant": "Dominant", "submissive": "Submissive", "switch": "Switch", "exhibitionist": "Exhibitionist"}
        if choice is None or choice.lower() not in classes:
            embed = discord.Embed(title="💠 Choose Your Echo Archetype", color=0x00fbff)
            embed.description = "**Dominant**: +20% Echo XP Bonus\n**Submissive**: +20% Sparks Bonus\n**Switch**: +10% Sparks & XP Bonus\n**Exhibitionist**: 15% Faster Cooldowns"
            embed.set_footer(text="Use !setclass <name>")
            return await ctx.send(embed=embed)
        self.cursor.execute("UPDATE users SET class_type = ? WHERE user_id = ?", (classes[choice.lower()], ctx.author.id))
        self.conn.commit()
        await ctx.send(f"✨ Your soul has harmonized with the **{classes[choice.lower()]}** archetype!")

    @commands.command(name="profile", aliases=["stats", "sparks"])
    async def profile(self, ctx, member: discord.Member = None):
        """Displays user profile."""
        if not self.check_premium(ctx.guild.id):
            return await ctx.send("🔒 The **ECONOMY ENGINE** is not active.")
        member = member or ctx.author
        sparks, xp, lvl, class_type = await self.get_user_data(member.id)
        xp_needed = lvl * 500
        embed = discord.Embed(title=f"✨ {member.display_name}'s Profile", color=0x00fbff)
        embed.add_field(name="🛡️ Archetype", value=f"**{class_type}**", inline=False)
        embed.add_field(name="⚡ Sparks", value=f"**{sparks:,}**", inline=True)
        embed.add_field(name="💠 Echo Level", value=f"Level **{lvl}**", inline=True)
        progress = int((xp / xp_needed) * 10)
        bar = "▰" * progress + "▱" * (10 - progress)
        embed.add_field(name="📊 Echo Experience", value=f"{bar} ({xp}/{xp_needed} XP)", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    # --- WORK CATEGORY COMMANDS ---

    @commands.command(name="work")
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def work(self, ctx):
        """Earn Sparks and XP through minor tasks (3h CD)"""
        await self.execute_work(ctx)

    @commands.command(name="clean")
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def clean(self, ctx):
        """Clean the Sanctuary floors."""
        await self.execute_work(ctx)

    @commands.command(name="beg")
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def beg(self, ctx):
        """Beg for Sparks in the Echo-Plaza."""
        await self.execute_work(ctx)

    @commands.command(name="slut")
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def slut(self, ctx):
        """Sell your Echo-energy on the street."""
        await self.execute_work(ctx)

    @commands.command(name="farm")
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def farm(self, ctx):
        """Harvest resources from the Spark-Fields."""
        await self.execute_work(ctx)

    @commands.command(name="cook")
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def cook(self, ctx):
        """Prepare Echo-infused meals for travelers."""
        await self.execute_work(ctx)

    @commands.command(name="mine")
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def mine(self, ctx):
        """Extract raw crystals from the Sanctuary mines."""
        await self.execute_work(ctx)

    # --- JOB CATEGORY COMMANDS ---

    @commands.command(name="job")
    @commands.cooldown(1, 18000, commands.BucketType.user)
    async def job(self, ctx):
        """Earn Sparks and XP through high-tier contracts (5h CD)"""
        await self.execute_job(ctx)

    @commands.command(name="crime")
    @commands.cooldown(1, 18000, commands.BucketType.user)
    async def crime(self, ctx):
        """Attempt a high-stakes Echo-heist."""
        await self.execute_job(ctx)

    @commands.command(name="pimp")
    @commands.cooldown(1, 18000, commands.BucketType.user)
    async def pimp(self, ctx):
        """Manage a ring of Echo-energy sellers."""
        await self.execute_job(ctx)

    @commands.command(name="hack")
    @commands.cooldown(1, 18000, commands.BucketType.user)
    async def hack(self, ctx):
        """Breach a high-security Sanctuary data-node."""
        await self.execute_job(ctx)

    @commands.command(name="assassinate")
    @commands.cooldown(1, 18000, commands.BucketType.user)
    async def assassinate(self, ctx):
        """Take down a rogue entity threatening the Echo-Chamber."""
        await self.execute_job(ctx)

    @commands.command(name="smuggle")
    @commands.cooldown(1, 18000, commands.BucketType.user)
    async def smuggle(self, ctx):
        """Transport illegal Echo-crystals past Sanctuary guards."""
        await self.execute_job(ctx)

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
            # Safe catch for archetype check
            class_type = data[3] if data else "None"
            retry_after = error.retry_after * 0.85 if class_type == "Exhibitionist" else error.retry_after
            minutes, seconds = divmod(retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            await ctx.send(f"⏳ Patience! You can earn more in **{int(hours)}h {int(minutes)}m {int(seconds)}s**.")

async def setup(bot):
    await bot.add_cog(Bank(bot))
