import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import datetime
import os
import json
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WELCOME_CHANNEL_ID = 1371961983250857985

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

BIRTHDAY_FILE = "birthdays.json"
REACTION_FILE = "reaction_roles.json"
TRACKING_FILE = "reaction_tracking.json"


# Load/save birthday data
def load_birthdays():
    if not os.path.exists(BIRTHDAY_FILE):
        return {}
    with open(BIRTHDAY_FILE, "r") as f:
        return json.load(f)


def save_birthdays(data):
    with open(BIRTHDAY_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Welcome messages
funny_comments = [
    "They've finally joined the cult—err, team! 🎭",
    "Quick, pretend we're doing something productive. 👀",
    "Another victim! Let's pretend we know what we're doing. 🤓",
    "Welcome! May your bugs be features. 🐛✨",
    "Caution: May spontaneously combust under pressure. 💥"
]

ascii_frame = """
╔════════════════════════════════╗
║ 🎮 A Wild Member Has Appeared! ║
╚════════════════════════════════╝
"""


@bot.event
async def on_ready():
    await tree.sync()
    birthday_check.start()
    print(f"{bot.user} is online!")


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(
            f"{ascii_frame}\nWelcome {member.mention}! {random.choice(funny_comments)}"
        )


# DAILY BIRTHDAY CHECK
@tasks.loop(hours=24)
async def birthday_check():
    today = datetime.datetime.now().strftime("%m-%d")
    data = load_birthdays()
    for user_id, date_str in data.items():
        if date_str[5:] == today:
            birth_year = int(date_str[:4])
            age = datetime.datetime.now().year - birth_year
            user = await bot.fetch_user(int(user_id))
            channel = bot.get_channel(WELCOME_CHANNEL_ID)
            if user and channel:
                await channel.send(
                    f"🎉 It's {user.mention}'s birthday today! They're now {age} years old! What a noob in life! ;P"
                )


# ========= BIRTHDAY COMMANDS =========
@tree.command(name="set-birthday", description="Set your birthday (only once)")
@app_commands.describe(date="Your birthday (e.g. 2002-06-15)")
async def set_birthday(interaction: discord.Interaction, date: str):
    user_id = str(interaction.user.id)
    data = load_birthdays()
    if user_id in data:
        await interaction.response.send_message(
            "❌ You already set your birthday!", ephemeral=True)
        return
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
        data[user_id] = date
        save_birthdays(data)
        await interaction.response.send_message(f"✅ Birthday set to `{date}`!",
                                                ephemeral=True)
    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid date format. Use YYYY-MM-DD.", ephemeral=True)


@tree.command(name="set-user-birthday",
              description="Admin: Set someone else's birthday")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(date="Birthday (e.g. 2002-06-15)", member="Target user")
async def set_user_birthday(interaction: discord.Interaction, date: str,
                            member: discord.Member):
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
        data = load_birthdays()
        data[str(member.id)] = date
        save_birthdays(data)
        await interaction.response.send_message(
            f"🎂 Birthday for {member.mention} set to `{date}`!",
            ephemeral=False)
    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid date format. Use YYYY-MM-DD.", ephemeral=True)


@tree.command(name="birthday", description="Check someone's birthday")
@app_commands.describe(member="User to check")
async def birthday(interaction: discord.Interaction, member: discord.Member):
    data = load_birthdays()
    user_id = str(member.id)
    if user_id in data:
        date = data[user_id]
        birth_year = int(date[:4])
        age = datetime.datetime.now().year - birth_year
        await interaction.response.send_message(
            f"📅 {member.mention}'s birthday is `{date}` ({age} y/o)")
    else:
        await interaction.response.send_message(
            "❌ Birthday not set for that user.")


@tree.command(name="next-birthdays", description="See upcoming birthdays")
async def next_birthdays(interaction: discord.Interaction):
    data = load_birthdays()
    today = datetime.datetime.now()
    upcoming = []

    for user_id, date_str in data.items():
        user_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        upcoming_date = user_date.replace(year=today.year)
        if upcoming_date < today:
            upcoming_date = upcoming_date.replace(year=today.year + 1)
        upcoming.append((upcoming_date, user_id, user_date.year))

    upcoming.sort()
    lines = []
    for date, user_id, year in upcoming[:5]:
        user = await bot.fetch_user(int(user_id))
        age = date.year - year
        lines.append(f"{date.strftime('%d %B %Y')} – {user.mention} ({age})")

    if lines:
        await interaction.response.send_message("🎉 **Upcoming Birthdays:**\n" +
                                                "\n".join(lines))
    else:
        await interaction.response.send_message("No upcoming birthdays found.")


# ========= REACTION ROLES =========
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_reaction_roles(ctx):
    if not os.path.exists(REACTION_FILE):
        await ctx.send("❌ reaction_roles.json not found.")
        return

    with open(REACTION_FILE, "r") as f:
        config = json.load(f)

    with open(TRACKING_FILE, "w") as log:
        for group in config:
            channel = discord.utils.get(ctx.guild.text_channels,
                                        name=group["channel_name"])
            if channel:
                embed = discord.Embed(title=group["message_title"],
                                      color=discord.Color.blue())
                role_lines = [
                    f"{emoji} → `{role}`"
                    for emoji, role in group["roles"].items()
                ]
                embed.description = "\n".join(role_lines)
                message = await channel.send(embed=embed)

                for emoji in group["roles"]:
                    await message.add_reaction(emoji)

                log.write(
                    json.dumps({
                        "message_id": message.id,
                        "channel_id": channel.id,
                        "roles": group["roles"]
                    }) + "\n")

        await ctx.send("✅ Reaction role messages posted!")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    with open(REACTION_FILE, "r") as f:
        config = json.load(f)

    for group in config:
        guild = bot.get_guild(payload.guild_id)
        channel = discord.utils.get(guild.text_channels,
                                    name=group["channel_name"])
        if not channel or payload.channel_id != channel.id:
            continue

        role_name = group["roles"].get(str(payload.emoji))
        if not role_name:
            continue

        member = guild.get_member(payload.user_id)
        role = discord.utils.get(guild.roles, name=role_name)
        if member and role:
            # Limit dev roles to 2
            if "Dev Role" in group["message_title"]:
                current_dev_roles = [
                    r for r in member.roles
                    if r.name in group["roles"].values()
                ]
                if len(current_dev_roles) >= 2:
                    await channel.send(
                        f"{member.mention}, you can only have 2 Dev Roles!",
                        delete_after=5)
                    return
            try:
                await member.add_roles(role, reason="Reaction role added")
            except discord.Forbidden:
                pass


@bot.event
async def on_raw_reaction_remove(payload):
    with open(REACTION_FILE, "r") as f:
        config = json.load(f)

    for group in config:
        guild = bot.get_guild(payload.guild_id)
        channel = discord.utils.get(guild.text_channels,
                                    name=group["channel_name"])
        if not channel or payload.channel_id != channel.id:
            continue

        role_name = group["roles"].get(str(payload.emoji))
        if not role_name:
            continue

        member = guild.get_member(payload.user_id)
        role = discord.utils.get(guild.roles, name=role_name)
        if member and role:
            try:
                await member.remove_roles(role, reason="Reaction role removed")
            except discord.Forbidden:
                pass


# ========= UTIL COMMANDS =========
@bot.command()
async def guide(ctx):
    embed = discord.Embed(title="📘 Game Dev Bot Help",
                          color=discord.Color.blurple())
    embed.add_field(name="/set-birthday",
                    value="Set your birthday (only once)",
                    inline=False)
    embed.add_field(name="/birthday",
                    value="Check someone's birthday",
                    inline=False)
    embed.add_field(name="/next-birthdays",
                    value="See upcoming birthdays",
                    inline=False)
    embed.add_field(name="/schedule", value="Team meeting times", inline=False)
    embed.add_field(name="/pitch [Idea]", value="Submit a game pitch", inline=False)
    embed.add_field(name="/suggest [Idea]", value="Suggest a feature", inline=False)
    embed.add_field(name="/whoami", value="See your roles", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def whoami(ctx):
    roles = [r.name for r in ctx.author.roles if r.name != "@everyone"]
    await ctx.send(
        f"{ctx.author.mention}, your current roles: {', '.join(roles) or 'None'}"
    )


@bot.command()
async def schedule(ctx):
    await ctx.send(
        "📅 **Upcoming Meetings:**\n• Sunday 7PM – Pitch Review\n• Wednesday 8PM – Dev Sync\n• Friday 6PM – Playtest"
    )


@bot.command()
async def pitch(ctx, *, idea: str):
    await ctx.send(f"📢 **Pitch from {ctx.author.mention}**:\n> {idea}")


@bot.command()
async def suggest(ctx, *, idea: str):
    embed = discord.Embed(title="💡 Suggestion",
                          description=idea,
                          color=discord.Color.green())
    embed.set_footer(text=f"Suggested by {ctx.author.display_name}")
    channel = discord.utils.get(ctx.guild.text_channels, name="suggestions")
    if channel:
        await channel.send(embed=embed)
        await ctx.send("✅ Your suggestion was submitted.")
    else:
        await ctx.send("❌ #suggestions channel not found.")


# Start bot
bot.run(TOKEN)
