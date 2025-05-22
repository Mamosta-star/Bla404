import discord
from discord.ext import commands, tasks
import asyncio
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

pending_registrations = {}
approved_users = {}
reminders = []

logo_url = "https://cdn.discordapp.com/attachments/1374482705021931641/1374778753452081224/IMG_3540.png"

@tasks.loop(minutes=1)
async def check_reminders():
    now = datetime.datetime.now()
    for reminder in reminders[:]:
        if now >= reminder["time"]:
            try:
                await reminder["channel"].send(f"⏰ یادیاریت: {reminder['text']}")
            except:
                pass
            reminders.remove(reminder)

@bot.event
async def on_ready():
    print(f"✅ Bot tya: {bot.user}")
    check_reminders.start()

@bot.command(name="sendjoinmsg")
@commands.has_permissions(administrator=True)
async def send_join_message(ctx):
    join_button = discord.ui.Button(label="📝 کلیک بکە بۆ تۆماربوون", style=discord.ButtonStyle.green)

    async def join_callback(interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild

        if user.id in pending_registrations:
            await interaction.response.send_message("🕒 تۆ پێشتر تۆماربوویت.", ephemeral=True)
            return

        existing_channel = discord.utils.get(guild.text_channels, name=f"cv-player-{user.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(f"🔒 تیکەتت پێشتر دروست بووە: {existing_channel.mention}", ephemeral=True)
            return

        category = discord.utils.get(guild.categories, name="CV Players")
        if not category:
            category = await guild.create_category("CV Players")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(f"cv-player-{user.name}", category=category, overwrites=overwrites)

        await interaction.response.send_message(f"✅ تیکەتت دروست کرایەوە: {channel.mention}", ephemeral=True)

        def check(m):
            return m.author == user and m.channel == channel

        try:
            await channel.send("🎮 **سڵاو! تکایە پرسیارەکان وەلام بدە:**")

            await channel.send("1️⃣ ناوت:")
            name = (await bot.wait_for('message', check=check, timeout=120)).content

            await channel.send("2️⃣ تەمەن:")
            age = (await bot.wait_for('message', check=check, timeout=60)).content

            await channel.send("3️⃣ PC یان Mobile؟")
            device = (await bot.wait_for('message', check=check, timeout=60)).content

            await channel.send("4️⃣ شوێن:")
            location = (await bot.wait_for('message', check=check, timeout=60)).content

            await channel.send("5️⃣ بردووت لە تۆرنۆمەنت؟ (بەڵێ/نەخێر)")
            tournament = (await bot.wait_for('message', check=check, timeout=60)).content

            await channel.send("6️⃣ eFootball ID:")
            efootball_id = (await bot.wait_for('message', check=check, timeout=60)).content

            pending_registrations[user.id] = {
                "name": name,
                "age": age,
                "device": device,
                "location": location,
                "tournament": tournament,
                "efootball_id": efootball_id
            }

            await channel.send("✅ زانیاریەکانت نێردران بۆ ئەدمین.")

            log_channel = discord.utils.get(guild.text_channels, name="🗂ticket-log")
            if log_channel:
                embed = discord.Embed(title="📝 CV نوێ", color=0x2ecc71)
                embed.set_author(name=str(user), icon_url=user.display_avatar.url)
                embed.add_field(name="👤 ناو", value=name, inline=True)
                embed.add_field(name="📅 تەمەن", value=age, inline=True)
                embed.add_field(name="💻 ئامێر", value=device, inline=True)
                embed.add_field(name="🌍 شوێن", value=location, inline=True)
                embed.add_field(name="🏆 تۆرنۆمەنت", value=tournament, inline=True)
                embed.add_field(name="🆔 eFootball ID", value=efootball_id, inline=True)
                embed.set_footer(text="ROVER GAMING", icon_url=logo_url)
                await log_channel.send(embed=embed)

        except asyncio.TimeoutError:
            await channel.send("⏱️ کاتت تێپەڕی، دووبارە هەوڵ بدە.")

    join_button.callback = join_callback
    view = discord.ui.View()
    view.add_item(join_button)

    await ctx.send("🎮 **کلیک بکە بۆ داگرتنی تیکەت و پڕکردنەوەی CV:**", view=view)

@bot.command(name="accept")
@commands.has_permissions(administrator=True)
async def accept(ctx, member: discord.Member):
    if member.id not in pending_registrations:
        await ctx.send("❌ ئەم بەکارهێنەرە تۆمار نەکراوە.")
        return

    approved_users[member.id] = pending_registrations.pop(member.id)

    role = discord.utils.get(ctx.guild.roles, name="🎮 Player")
    if role:
        await member.add_roles(role)

    await ctx.send(f"✅ {member.name} پشتڕاست کرا و ڕۆڵی بەشدارەکان پێدرا.")

    try:
        await member.send("🎉 بەخێربێیت! تۆ پشتڕاست کراییت و ڕۆڵی یاریزانی پێدرا.")
    except discord.Forbidden:
        await ctx.send("⚠️ ناتوانم نامە بنێرم.")

@bot.command(name="reject")
@commands.has_permissions(administrator=True)
async def reject(ctx, member: discord.Member):
    if member.id not in pending_registrations:
        await ctx.send("❌ ئەم بەکارهێنەرە تۆمار نەکراوە.")
        return

    pending_registrations.pop(member.id)
    await ctx.send(f"🚫 {member.name} ڕەتکرایەوە.")

    try:
        await member.send("❗ داواکارییەکەت ڕەتکرایەوە.")
    except discord.Forbidden:
        await ctx.send("⚠️ ناتوانم نامە بنێرم.")

@bot.command(name="remind")
async def remind(ctx, *, msg):
    try:
        parts = msg.rsplit(" ", 1)
        text = parts[0]
        time = parts[1]
        units = {"s": 1, "m": 60, "h": 3600}
        seconds = int(time[:-1]) * units[time[-1]]
        remind_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        reminders.append({"time": remind_time, "text": text, "channel": ctx.channel})
        await ctx.send("✅ یادیاری زیادکرا")
    except:
        await ctx.send("❌ هەڵە لە نوسین")

@bot.command(name="broadcast")
@commands.has_permissions(administrator=True)
async def broadcast(ctx, *, msg):
    role = discord.utils.get(ctx.guild.roles, name="🎮 Player")
    if not role:
        await ctx.send("❌ ڕۆڵی یاریزان نەدۆزرایەوە")
        return
    for member in role.members:
        try:
            await member.send(msg)
        except:
            pass
    await ctx.send("📢 پەیام نێردرا بۆ هەموو یاریزانەکان")

@bot.command(name="stats")
async def stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    if member.id not in approved_users:
        await ctx.send("❌ ئەم بەکارهێنەرە تۆمار نەکراوە.")
        return

    data = approved_users[member.id]
    embed = discord.Embed(title="📊 زانیاریی یاریزان", color=0x3498db)
    embed.set_author(name=str(member), icon_url=member.display_avatar.url)
    for key, value in data.items():
        embed.add_field(name=key, value=value, inline=False)
    await ctx.send(embed=embed)

bot.run("")
