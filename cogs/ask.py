import discord
from discord.ext import commands
import io
import aiohttp
import os
import json
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageOps
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
        # Professional standard: Add the Fiery Logo as a thumbnail to EVERY embed
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_thumbnail(url="attachment://thumb.png")
        return embed

    def get_logo(self):
        # Utility to grab the logo file for the embed
        if os.path.exists("fierylogo.jpg"):
            return discord.File("fierylogo.jpg", filename="thumb.png")
        return None

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
            # maximized borderless visual engine
            canvas = Image.new("RGBA", (1200, 600), (10, 0, 5, 255))
            draw = ImageDraw.Draw(canvas)
            async with aiohttp.ClientSession() as session:
                async with session.get(u1_url) as r1, session.get(u2_url) as r2:
                    p1, p2 = io.BytesIO(await r1.read()), io.BytesIO(await r2.read())
            
            av_size = 420 # Increased size for maximization
            av1_raw = Image.open(p1).convert("RGBA").resize((av_size, av_size))
            av2_raw = Image.open(p2).convert("RGBA").resize((av_size, av_size))

            # Borderless circular clipping
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, av_size, av_size), fill=255)
            
            av1 = ImageOps.fit(av1_raw, mask.size, centering=(0.5, 0.5))
            av1.putalpha(mask)
            av2 = ImageOps.fit(av2_raw, mask.size, centering=(0.5, 0.5))
            av2.putalpha(mask)
            
            def draw_aura(draw_obj, pos, size, color):
                for i in range(25, 0, -1):
                    alpha = int(140 * (1 - i/25))
                    draw_obj.ellipse([pos[0]-i, pos[1]-i, pos[0]+size+i, pos[1]+size+i], outline=(*color, alpha), width=3)
            
            draw_aura(draw, (70, 90), av_size, (255, 20, 147)) 
            draw_aura(draw, (710, 90), av_size, (255, 69, 0))   
            
            canvas.paste(av1, (70, 90), av1)
            canvas.paste(av2, (710, 90), av2)
            
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
        logo = self.get_logo()
        if member is None:
            return await ctx.send(file=logo, embed=self.fiery_embed("🔞 WHO'S THE TARGET?", "You need to mention someone to start the heat..."))
        
        if member.id == ctx.author.id:
            return await ctx.send("Try asking someone else, love.")

        guild_id = str(ctx.guild.id)
        is_premium = guild_id in __main__.PREMIUM_GUILDS and self.module_name in __main__.PREMIUM_GUILDS[guild_id]
        
        files = []
        if logo: files.append(logo)

        if is_premium:
            img = await self.create_premium_lobby(ctx.author.display_avatar.url, member.display_avatar.url)
            files.append(discord.File(img, filename="ask.png"))
            emb = self.fiery_embed("✨ A NEW CONNECTION IS BREWING...", f"**{ctx.author.display_name}** is looking at **{member.display_name}** with interest...")
            emb.set_image(url="attachment://ask.png")
        else:
            emb = self.fiery_embed("🔥 SOMETHING'S STARTING...", f"{ctx.author.mention} wants to get close to {member.mention}.\n\n*Unlock the full visual experience with !premium*")

        class InitialView(discord.ui.View):
            def __init__(self, cog, r, t):
                super().__init__(timeout=120)
                self.cog, self.r, self.t = cog, r, t

            @discord.ui.button(label="Ask to DM", style=discord.ButtonStyle.primary, emoji="🫦")
            async def dm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.r.id: return
                
                options = [
                    discord.SelectOption(label="Polite & Sweet (SFW)", value="SFW", emoji="😇"),
                    discord.SelectOption(label="Wild & Lustful (NSFW)", value="NSFW", emoji="🔞"),
                    discord.SelectOption(label="Just Vibe", value="Casual", emoji="🍹")
                ]
                select = discord.ui.Select(placeholder="What's your mood?", options=options)

                async def callback(i: discord.Interaction):
                    intent = select.values[0]
                    logo_callback = self.cog.get_logo()
                    
                    if intent == "NSFW":
                        mood_title = "🫦 A TANTALIZING INVITATION"
                        mood_desc = f"{self.t.mention}, {self.r.mention} wants to dive into the **deep end** with you. Do you accept the heat?"
                        mood_color = 0xff0066 
                        acc_label = "Say Yes..."
                        den_label = "Not Tonight"
                    else:
                        mood_title = "👋 HEY THERE..."
                        mood_desc = f"{self.t.mention}, {self.r.mention} is reaching out for a **{intent}** chat. Want to talk?"
                        mood_color = 0xffa500 
                        acc_label = "Sure!"
                        den_label = "No! Maybe later, sorry"

                    class RecView(discord.ui.View):
                        def __init__(self, cog, r, t, it):
                            super().__init__(timeout=300)
                            self.cog, self.r, self.t, self.it = cog, r, t, it

                        @discord.ui.button(label=acc_label, style=discord.ButtonStyle.success, emoji="🔥")
                        async def acc(self, inner_i, b):
                            if inner_i.user.id != self.t.id: return
                            self.cog.log_ask_event(self.r, self.t, self.it, "Accepted")
                            await inner_i.response.send_message(f"✨ YES {self.r.mention}")

                        @discord.ui.button(label=den_label, style=discord.ButtonStyle.danger, emoji="🥀")
                        async def den(self, inner_i, b):
                            if inner_i.user.id != self.t.id: return
                            self.cog.log_ask_event(self.r, self.t, self.it, "Denied")
                            await inner_i.response.send_message(f"😭 No {self.r.mention}")

                    final_emb = self.cog.fiery_embed(mood_title, mood_desc, mood_color)
                    await i.response.send_message(content=self.t.mention, embed=final_emb, view=RecView(self.cog, self.r, self.t, intent), file=logo_callback)
                
                select.callback = callback
                v = discord.ui.View(); v.add_item(select)
                await interaction.response.send_message("Choose your vibe:", view=v, ephemeral=True)

        await ctx.send(files=files, embed=emb, view=InitialView(self, ctx.author, member))

    @commands.command(name="askcommands")
    async def askcommands(self, ctx):
        logo = self.get_logo()
        embed = self.fiery_embed("🔥 THE FIERY SYSTEM 🔥", "What can we do tonight?")
        embed.add_field(name="📩 Connections", value="`!ask @user` | `!invite`", inline=False)
        embed.add_field(name="💎 Premium", value="`!premium` | `!premiumstatus`", inline=False)
        await ctx.send(file=logo, embed=embed)

    @commands.command(name="askpremium")
    @commands.has_permissions(administrator=True)
    async def askpremium(self, ctx):
        logo = self.get_logo()
        pay_email = os.getenv('PAYPAL_EMAIL')
        custom_payload = f"{ctx.guild.id}|{self.module_name}"
        paypal_link = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={pay_email}&amount=2.50&currency_code=USD&item_name=Premium_Server_{ctx.guild.id}&custom={custom_payload}"
        embed = self.fiery_embed("💎 UPGRADE THE EXPERIENCE", f"Click [**HERE**]({paypal_link}) to unlock Premium.\n\n• Borderless Visual Lobbies\n• Maximized Avatars")
        await ctx.send(file=logo, embed=embed)

    @commands.command(name="adminask")
    @commands.has_permissions(administrator=True)
    async def adminask(self, ctx):
        logo = self.get_logo()
        guild_id = str(ctx.guild.id)
        is_premium = guild_id in __main__.PREMIUM_GUILDS and self.module_name in __main__.PREMIUM_GUILDS[guild_id]
        if not is_premium:
            return await ctx.send(file=logo, embed=self.fiery_embed("🚫 LOCKED", "History is a premium feature."))
        
        if not os.path.exists(self.HISTORY_FILE):
            return await ctx.send(file=logo, embed=self.fiery_embed("📊 RECENT SPARKS", "Silence... for now."))
        
        with open(self.HISTORY_FILE, "r") as f:
            logs = json.load(f)
        recent = "\n".join([f"• {e['requester']} ➡️ {e['target']} ({e['status']})" for e in logs[-10:]])
        await ctx.send(file=logo, embed=self.fiery_embed("📊 RECENT SPARKS", recent))

    @commands.command(name="askactivate")
    @commands.is_owner()
    async def askactivate(self, ctx, guild_id: str):
        if guild_id not in __main__.PREMIUM_GUILDS:
            __main__.PREMIUM_GUILDS[guild_id] = []
        if self.module_name not in __main__.PREMIUM_GUILDS[guild_id]:
            __main__.PREMIUM_GUILDS[guild_id].append(self.module_name)
            with open(self.PREMIUM_FILE, "w") as f:
                json.dump(__main__.PREMIUM_GUILDS, f)
        await ctx.send(f"✅ **{self.module_name.upper()}** module activated!")

    @commands.command(name="askon")
    @commands.is_owner()
    async def askon(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in __main__.PREMIUM_GUILDS: __main__.PREMIUM_GUILDS[guild_id] = []
        if self.module_name not in __main__.PREMIUM_GUILDS[guild_id]: __main__.PREMIUM_GUILDS[guild_id].append(self.module_name)
        await ctx.send("🛠️ **DEV MODE:** Premium ON.")

    @commands.command(name="askoff")
    @commands.is_owner()
    async def askoff(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in __main__.PREMIUM_GUILDS and self.module_name in __main__.PREMIUM_GUILDS[guild_id]: __main__.PREMIUM_GUILDS[guild_id].remove(self.module_name)
        await ctx.send("🛠️ **DEV MODE:** Premium OFF.")

async def setup(bot):
    await bot.add_cog(DungeonAsk(bot))
