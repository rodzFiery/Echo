import discord
from discord.ext import commands
import sqlite3
import os
import random
import __main__

class Bank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Database Setup - Using Railway Volume (DATA_DIR from your main.py)
        # We use the same directory /app/data to ensure persistence
        db_path = "/app/data/economy.db" if os.path.exists("/app/data") else "economy.db"
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS bank 
                              (user_id INTEGER PRIMARY KEY, wallet INTEGER DEFAULT 0, bank INTEGER DEFAULT 0)''')
        self.conn.commit()

    def check_premium(self, guild_id):
        # Access global PREMIUM_GUILDS from main.py
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        guild_id_str = str(guild_id)
        # Pulling the shared premium list from your main script
        premium_data = getattr(__main__, 'PREMIUM_GUILDS', {})
        guild_mods = premium_data.get(guild_id_str, {})
        # Checking specifically for 'bank' module access
        expiry = guild_mods.get('bank', 0)
        return expiry > now

    async def open_account(self, user_id):
        self.cursor.execute("SELECT wallet FROM bank WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        if result is None:
            # Starting balance of $100 for new users
            self.cursor.execute("INSERT INTO bank (user_id, wallet, bank) VALUES (?, ?, ?)", (user_id, 100, 0))
            self.conn.commit()
            return True
        return False

    async def get_balance(self, user_id):
        await self.open_account(user_id)
        self.cursor.execute("SELECT wallet, bank FROM bank WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    @commands.command(name="balance", aliases=["bal"])
    async def balance(self, ctx, member: discord.Member = None):
        # Premium Check Integrated with main.py logic
        if not self.check_premium(ctx.guild.id):
            embed = discord.Embed(title="🔒 MODULE LOCKED", color=0xff0000)
            embed.description = "The **BANK** module is not active. An administrator must use `!premium` to unlock the economy system."
            return await ctx.send(embed=embed)

        member = member or ctx.author
        wallet, bank = await self.get_balance(member.id)

        embed = discord.Embed(title=f"🏦 {member.display_name}'s Vault", color=0xffd700)
        embed.add_field(name="💰 Wallet", value=f"${wallet:,}", inline=True)
        embed.add_field(name="🏛️ Bank", value=f"${bank:,}", inline=True)
        embed.add_field(name="📊 Total", value=f"${(wallet + bank):,}", inline=False)
        
        if os.path.exists("fierylogo.jpg"):
            file = discord.File("fierylogo.jpg", filename="fierylogo.jpg")
            embed.set_thumbnail(url="attachment://fierylogo.jpg")
            await ctx.send(file=file, embed=embed)
        else:
            embed.set_thumbnail(url=member.display_avatar.url)
            await ctx.send(embed=embed)

    @commands.command(name="deposit", aliases=["dep"])
    async def deposit(self, ctx, amount=None):
        wallet, bank = await self.get_balance(ctx.author.id)
        if amount is None:
            return await ctx.send("⚠️ Please specify an amount to deposit.")
        
        if amount.lower() == "all":
            amount = wallet
        else:
            amount = int(amount)

        if amount > wallet:
            return await ctx.send("⚠️ You don't have that much in your wallet!")
        if amount <= 0:
            return await ctx.send("⚠️ Amount must be positive!")

        self.cursor.execute("UPDATE bank SET wallet = wallet - ?, bank = bank + ? WHERE user_id = ?", (amount, amount, ctx.author.id))
        self.conn.commit()
        await ctx.send(f"✅ Deposited **${amount:,}** into your bank!")

    @commands.command(name="withdraw", aliases=["with"])
    async def withdraw(self, ctx, amount=None):
        wallet, bank = await self.get_balance(ctx.author.id)
        if amount is None:
            return await ctx.send("⚠️ Please specify an amount to withdraw.")
        
        if amount.lower() == "all":
            amount = bank
        else:
            amount = int(amount)

        if amount > bank:
            return await ctx.send("⚠️ You don't have that much in your bank!")
        if amount <= 0:
            return await ctx.send("⚠️ Amount must be positive!")

        self.cursor.execute("UPDATE bank SET bank = bank - ?, wallet = wallet + ? WHERE user_id = ?", (amount, amount, ctx.author.id))
        self.conn.commit()
        await ctx.send(f"✅ Withdrew **${amount:,}** from your bank!")

    @commands.command(name="beg")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def beg(self, ctx):
        if not self.check_premium(ctx.guild.id):
            return await ctx.send("🔒 Unlock the **BANK** module to use the `beg` command.")
            
        earnings = random.randint(10, 50)
        self.cursor.execute("UPDATE bank SET wallet = wallet + ? WHERE user_id = ?", (earnings, ctx.author.id))
        self.conn.commit()
        await ctx.send(f"🤲 Someone felt generous and gave you **${earnings}**!")

async def setup(bot):
    await bot.add_cog(Bank(bot))
