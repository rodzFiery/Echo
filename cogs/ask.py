import discord
from discord.ext import commands
import io
import aiohttp
import os
import json
from datetime import datetime, timezone
from PIL import Image, ImageDraw
import __main__ # Access the premium list from main.py

class DungeonAsk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module_name = "ask"
        # Paths for persistent storage
        self.DATA_DIR = "/app/data"
        self.HISTORY_FILE = os.path.join(self.DATA_DIR, "ask_history.json")
        self.PREMIUM_FILE = os.path.join(self.DATA_DIR, "premium_guilds.json")

    # --- UTILITIES ---
    def fiery_embed(self, title, description, color=0xff4500):
        return discord.Embed(title=title, description=description, color=color)

    def log_ask_event(self, requester, target, intent, status):
        data = []
        if os.path.exists(self.HISTORY_FILE):
            with open(self.HISTORY_FILE, "r") as f:
                try:
                    data = json.load(f)
                except:
                    data = []
        
        data.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requester": str(requester),
            "target": str(target),
            "intent": intent,
            "status": status
        })
        
        with open(self.HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=4)

    # --- IMAGE ENGINE (PREMIUM) ---
    async def create_premium_lobby(self, u1_url, u2_url):
        try:
            # Renders a high-level visual with BOTH user avatars
            canvas = Image.new("RGBA", (1200, 600), (15, 0, 8, 255))
            draw = ImageDraw.Draw(canvas)
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1, p2 = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())
            
            av1 = Image.open(p1).convert("RGBA").resize((350, 350))
            av2 = Image.open(p2).convert("RGBA").resize((350, 350))
            
            def draw_glow(draw_obj, pos, size, color):
                for i in range(15, 0, -1):
                    alpha = int(255 * (1 - i/15))
                    draw_obj.rectangle([pos[0]-i, pos[1]-i, pos[0]+size+i, pos[1]+size+i], outline=(*color, alpha), width=2)
            
            draw_glow(draw, (100, 120), 350, (255, 20, 147)) 
            draw_glow(draw, (750, 120), 350, (255, 0, 0))   
            canvas.paste(av1, (100, 120), av1)
            canvas.paste(av2, (750, 120), av2)
            draw.text((550, 250), "VS", fill=(255, 0, 0))
            
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Image Error: {e}")
            return None

    # --- COMMANDS ---
    @commands.command(name="ask")
    async def ask(self, ctx, member: discord.Member = None):
        if member is None:
            return await ctx.send(embed=self.fiery_embed("⚠️ ERROR", "You must mention a user!\nExample: `!ask @user`"))
        
        if member.id == ctx.author.id:
            return await ctx.send("❌ You cannot ask yourself.")

        # Access the modular premium dictionary from main.py
        guild_id = str(ctx.guild.id)
        is_premium = guild_id in __main__.PREMIUM_GUILDS and self.module_name in __main__.PREMIUM_GUILDS[guild_id]
        
        if is_premium:
            # Grabs both avatars for the Premium Lobby
            img = await self.create_premium_lobby(ctx.author.display_avatar.url, member.display_avatar.url)
            file = discord.File(img, filename="ask.png")
            emb = self.fiery_embed("💎 PREMIUM SIGNAL SENT", f"**{ctx.author.display_name}** ⚔️ **{member.display_name}**")
            emb.set_image(url="attachment://ask.png")
        else:
            file, emb = None, self.fiery_embed("🔥 CONNECTION REQUEST", f"{ctx.author.mention} is requesting a moment with {member.mention}.\n\n*Unlock the visual VS engine with !premium*")

        # Views for interaction
        class InitialView(discord.ui.View):
            def __init__(self, cog, r, t):
                super().__init__(timeout=120)
                self.cog, self.r, self.t = cog, r, t

            @discord.ui.button(label="Open Connection", style=discord.ButtonStyle.primary, emoji="📩")
            async def dm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.r.id: return
                
                options = [
                    discord.SelectOption(label="SFW / Professional", value="SFW", emoji="🛡️", description="Keep things clean and polite."),
                    discord.SelectOption(label="NSFW / Lustful", value="NSFW", emoji="🔞", description="Step into the heat of the dungeon."),
                    discord.SelectOption(label="Casual Chat", value="Casual", emoji="💬", description="Just a friendly conversation.")
                ]
                select = discord.ui.Select(placeholder="Select the nature of your visit...", options=options)

                async def callback(i: discord.Interaction):
                    intent = select.values[0]
                    
                    # --- DYNAMIC PERSONA ENGINE (Professional vs Flirty) ---
                    if intent == "NSFW":
                        mood_title = "🫦 LUSTFUL INVITATION"
                        mood_desc = f"{self.t.mention}, {self.r.mention} wants to explore the **NSFW** side of things with you. Do you give in?"
                        mood_color = 0xe91e63 # Lustful Pink
                        acc_label = "Surrender"
                        den_label = "Resist"
                        den_emoji = "🥀"
                    else:
                        mood_title = "📩 FORMAL REQUEST"
                        mood_desc = f"{self.t.mention}, {self.r.mention} is requesting a **{intent}** conversation."
                        mood_color = 0xff4500 # Professional Fiery Orange
                        acc_label = "Accept"
                        den_label = "Decline"
                        den_emoji = "🛡️"

                    class RecView(discord.ui.View):
                        def __init__(self, cog, r, t, it):
                            super().__init__(timeout=300)
                            self.cog, self.r, self.t, self.it = cog, r, t, it

                        @discord.ui.button(label=acc_label, style=discord.ButtonStyle.success, emoji="🔥")
                        async def acc(self, inner_i, b):
                            if inner_i.user.id != self.t.id: return
                            self.cog.log_ask_event(self.r, self.t, self.it, "Accepted")
                            msg = "The heat is rising... they said yes." if self.it == "NSFW" else "The connection has been established."
                            await inner_i.response.send_message(f"✅ **{msg}** {self.r.mention}")

                        @discord.ui.button(label=den_label, style=discord.ButtonStyle.danger, emoji=den_emoji)
                        async def den(self, inner_i, b):
                            if inner_i.user.id != self.t.id: return
                            self.cog.log_ask_event(self.r, self.t, self.it, "Denied")
                            msg = "Maybe you aren't ready for this fire yet." if self.it == "NSFW" else "The request was declined."
                            await inner_i.response.send_message(f"🥀 **{msg}** {self.r.mention}")

                    final_emb = discord.Embed(title=mood_title, description=mood_desc, color=mood_color)
                    await i.response.send_message(content=self.t.mention, embed=final_emb, view=RecView(self.cog, self.r, self.t, intent))
                
                select.callback = callback
                v = discord.ui.View(); v.add_item(select)
                await interaction.response.send_message("The dungeon doors are open. Choose your path:", view=v, ephemeral=True)

        await ctx.send(file=file, embed=emb, view=InitialView(self, ctx.author, member))

    @commands.command(name="askcommands")
    async def askcommands(self, ctx):
        embed = self.fiery_embed("🔥 ASK SYSTEM COMMANDS 🔥", "Available tools:")
        embed.add_field(name="📩 User", value="`!ask @user` - Create a professional/flirty lobby.\n`!invite` - Get bot link.", inline=False)
        embed.add_field(name="🛡️ Admin", value="`!premium` - Open the Fiery Shop.\n`!premiumstatus` - View server unlocks.", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="askpremium")
    @commands.has_permissions(administrator=True)
    async def askpremium(self, ctx):
        pay_email = os.getenv('PAYPAL_EMAIL')
        # Modular PayPal payload: "GUILD_ID|MODULE_NAME"
        custom_payload = f"{ctx.guild.id}|{self.module_name}"
        paypal_link = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={pay_email}&amount=2.50&currency_code=USD&item_name=Premium_Server_{ctx.guild.id}&custom={custom_payload}"
        embed = self.fiery_embed("💎 UPGRADE TO PREMIUM", f"Click [**HERE**]({paypal_link}) to pay $2.50 via PayPal.\n\n**Benefits:**\n• Glowing Visual VS Lobbies\n• Faster Activation")
        await ctx.send(embed=embed)

    @commands.command(name="adminask")
    @commands.has_permissions(administrator=True)
    async def adminask(self, ctx):
        guild_id = str(ctx.guild.id)
        is_premium = guild_id in __main__.PREMIUM_GUILDS and self.module_name in __main__.PREMIUM_GUILDS[guild_id]
        if not is_premium:
            return await ctx.send("🚫 **Admin History is a Premium Feature.** Unlock it in the `!premium` shop.")
        
        if not os.path.exists(self.HISTORY_FILE):
            return await ctx.send("No logs found.")
        
        with open(self.HISTORY_FILE, "r") as f:
            logs = json.load(f)
        
        recent = "\n".join([f"• {e['requester']} ➡️ {e['target']} ({e['status']})" for e in logs[-10:]])
        await ctx.send(embed=self.fiery_embed("📊 RECENT ACTIVITY", recent if recent else "No recent data."))

    @commands.command(name="askactivate")
    @commands.is_owner()
    async def askactivate(self, ctx, guild_id: str):
        if guild_id not in __main__.PREMIUM_GUILDS:
            __main__.PREMIUM_GUILDS[guild_id] = []
        
        if self.module_name not in __main__.PREMIUM_GUILDS[guild_id]:
            __main__.PREMIUM_GUILDS[guild_id].append(self.module_name)
            with open(self.PREMIUM_FILE, "w") as f:
                json.dump(__main__.PREMIUM_GUILDS, f)
            await ctx.send(f"✅ Module **{self.module_name}** activated for Guild {guild_id}!")

async def setup(bot):
    await bot.add_cog(DungeonAsk(bot))
