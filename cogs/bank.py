import discord
from discord.ext import commands
import sqlite3
import os
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
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                              (user_id INTEGER PRIMARY KEY, 
                               sparks INTEGER DEFAULT 100, 
                               echo_xp INTEGER DEFAULT 0, 
                               echo_level INTEGER DEFAULT 1)''')
        self.conn.commit()

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
            self.cursor.execute("INSERT INTO users (user_id, sparks, echo_xp, echo_level) VALUES (?, ?, ?, ?)", 
                               (user_id, 100, 0, 1))
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
        if new_xp >= xp_needed:
            new_xp -= xp_needed
            lvl += 1
            leveled_up = True
            
        self.cursor.execute("UPDATE users SET echo_xp = ?, echo_level = ? WHERE user_id = ?", 
                           (new_xp, lvl, user_id))
        self.conn.commit()
        return leveled_up, lvl

    async def get_user_data(self, user_id):
        """Fetches all engine data for a specific user."""
        await self.open_account(user_id)
        self.cursor.execute("SELECT sparks, echo_xp, echo_level FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    # --- USER COMMANDS ---

    @commands.command(name="profile", aliases=["stats", "sparks"])
    async def profile(self, ctx, member: discord.Member = None):
        """Displays the user's current Sparks and Echo Experience."""
        if not self.check_premium(ctx.guild.id):
            embed = discord.Embed(title="🔒 ENGINE LOCKED", color=0xff0000)
            embed.description = "The **ECONOMY ENGINE** is not active. An administrator must use `!premium` to unlock."
            return await ctx.send(embed=embed)

        member = member or ctx.author
        sparks, xp, lvl = await self.get_user_data(member.id)
        xp_needed = lvl * 500

        embed = discord.Embed(title=f"✨ {member.display_name}'s Profile", color=0x00fbff)
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

async def setup(bot):
    await bot.add_cog(Bank(bot))
