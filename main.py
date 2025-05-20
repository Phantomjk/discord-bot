import os
import json
import random
import asyncio
import discord
from dotenv import load_dotenv
from discord import app_commands
from datetime import date, datetime
from discord.ext import commands, tasks
from dateutil.relativedelta import relativedelta

with open("reaction_roles.json", "r", encoding="utf-8") as f:
    reaction_roles_config = {"reaction_role_groups": json.load(f)}

# Fix the welcome message [done]
# Fix the birthday so that it can include the days and months as well, for example (user) is 23 yrs old, 5 months, and 30 days old [done]
# Delete the last 5 messages in the message [done]
# Fix roles update [done]
# Fix the suggestion [done]

# Fix roles limits and addition
# Add a music yt to music converter and spotify playslist player 
# steal emojis and use them through the bot
# Add game roles (most famous to mention and play games)

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
SUGGESTION_CHANNEL_ID = int(os.getenv("SUGGESTION_CHANNEL_ID"))

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
    with open(BIRTHDAY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_birthdays(data):
    with open(BIRTHDAY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# Welcome messages
funny_comments = [
    "They've finally joined the cult—err, team! 🤫",
    "Quick, pretend we're doing something productive. 👀",
    "Another victim! Let's pretend we know what we're doing. 🤓",
    "Welcome! May your bugs be features. 🐛✨",
    "Caution: May spontaneously combust under pressure. 💥",
    "Welcome {mention}, you have been accused of the following crime: Hogging the remote control and changing channels frequently. How do you plead? Guilty or not guilty? 🧐",
    "Look who's here! {mention} just unlocked the 'Joined the Coolest Server' achievement! 🤩",
    "Ah, fresh meat—uh, we mean, welcome {mention}! 😈",
    "{mention}, brace yourself. The chaos starts now. 😬",
    "📺 Breaking News: {mention} has entered the server!"
]


ascii_frame = """
╔════════════════════════════════╗
║ 🎮 A Wild Member Has Appeared! ║
╚════════════════════════════════╝
"""


@bot.event
async def on_ready():
    await bot.tree.sync()
    birthday_check.start()
    print(f"{bot.user} is ready and slash commands are synced.")


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        # 1. Send random funny welcome message first
        welcome_msg = random.choice(funny_comments).replace("{mention}", member.mention)
        await channel.send(welcome_msg)

        # 2. Send the welcome image + embed
        file = discord.File("welcome.png", filename="welcome.png")
        embed = discord.Embed(
            title=f"👋 Hello {member.name}!",
            description="Welcome to the server!",
            color=discord.Color.green()
        )
        embed.set_image(url="attachment://welcome.png")
        await channel.send(file=file, embed=embed)

        await asyncio.sleep(0.5)

        # 3. Send role instructions
        await channel.send(
            f"{member.mention} Select your roles from <#1371961717394899045> then head to <#1072074904096231467> to start your journey.\n"
            "```diff\n+ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n```"
        )



# DAILY BIRTHDAY CHECK
@tasks.loop(hours=24)
async def birthday_check():
    today = datetime.now().strftime("%m-%d")
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
        datetime.strptime(date, "%Y-%m-%d")
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
        datetime.strptime(date, "%Y-%m-%d")
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
        date_str = data[user_id]
        birthday_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = date.today()
        diff = relativedelta(today, birthday_date)
        full_age = f"{diff.years} y/o, {diff.months} months, and {diff.days} days"
        await interaction.response.send_message(
            f"📅 {member.mention}'s birthday is `{date_str}` ({full_age})"
        )
    else:
        await interaction.response.send_message(
            "❌ Birthday not set for that user."
        )


@tree.command(name="next-birthdays", description="See upcoming birthdays")
async def next_birthdays(interaction: discord.Interaction):
    data = load_birthdays()
    today = datetime.now()
    upcoming = []

    for user_id, date_str in data.items():
        user_date = datetime.strptime(date_str, "%Y-%m-%d")
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
        await ctx.send("❌ `reaction_roles.json` not found.")
        return

    with open(REACTION_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    with open(TRACKING_FILE, "w", encoding="utf-8") as log:
        for group in config:
            channel = bot.get_channel(int(group["channel_id"]))
            if channel:
                embed = discord.Embed(title=group["message_title"], color=discord.Color.blue())
                role_lines = [f"{emoji} → `{role}`" for emoji, role in group["roles"].items()]
                embed.description = "\n".join(role_lines)
                message = await channel.send(embed=embed)

                for emoji in group["roles"]:
                    await message.add_reaction(emoji)

                log.write(json.dumps({
                    "message_id": message.id,
                    "channel_id": channel.id,
                    "roles": group["roles"]
                }) + "\n")

        await ctx.send("✅ Reaction role messages have been posted!")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member:
        return

    # Loop through all configured reaction role groups (FIXED INDENTATION)
    for group in reaction_roles_config["reaction_role_groups"]:
        if "message_id" not in group or "roles" not in group:
            continue  # Skip invalid configs

        if payload.message_id == int(group["message_id"]):
            role_name = group["roles"].get(payload.emoji.name)
            if not role_name:
                continue

            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                continue

            # 🧠 Dev Role limit check
            if "Dev Role" in group.get("message_title", ""):
                dev_roles = list(group["roles"].values())
                user_dev_roles = [r.name for r in member.roles if r.name in dev_roles]

                if len(user_dev_roles) >= 2:
                    try:
                        channel = bot.get_channel(payload.channel_id)
                        if channel:
                            message = await channel.fetch_message(payload.message_id)
                            await message.remove_reaction(payload.emoji, member)
                            await channel.send(
                                f"⚠️ {member.mention}, you can only choose **2** dev roles.",
                                delete_after=5
                            )
                    except Exception as e:
                        print(f"Error removing reaction: {e}")
                    return  # Stop here, don't assign

            # ✅ Assign role
            try:
                await member.add_roles(role)
                print(f"✅ Added role {role_name} to {member.display_name}")
            except discord.Forbidden:
                print(f"❌ Missing permissions to add role {role_name}")
            except Exception as e:
                print(f"❌ Error assigning role: {e}")


@bot.event
async def on_raw_reaction_remove(payload):
    with open(REACTION_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    for group in config:
        if int(group["channel_id"]) != payload.channel_id:
            continue

        emoji_roles = group["roles"]
        role_name = emoji_roles.get(str(payload.emoji))
        if not role_name:
            return

        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = discord.utils.get(guild.roles, name=role_name)

        if role and member:
            try:
                await member.remove_roles(role, reason="Reaction role removed")
            except discord.Forbidden:
                print(f"❌ Missing permission to remove role {role.name} from {member.name}")


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
    embed.add_field(name="/dfive", value="Deletes the last 5 messages", inline=False)
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

@tree.command(
    name="dfive",
    description="Deletes the last 5 messages in this channel."
)
@app_commands.checks.has_permissions(manage_messages=True)
async def dfive(interaction: discord.Interaction):
    if not interaction.channel.permissions_for(interaction.user).manage_messages:
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    await interaction.response.send_message("🧹 Cleaning up the last 5 messages...", ephemeral=True)

    try:
        deleted = await interaction.channel.purge(limit=5)
        await interaction.channel.send(f"✅ Deleted {len(deleted)} messages!", delete_after=3)
    except discord.Forbidden:
        await interaction.channel.send("❌ I don't have permission to delete messages in this channel.", delete_after=3)
    except Exception as e:
        await interaction.channel.send(f"⚠️ Error occurred: {str(e)}", delete_after=5)


@bot.command()
async def suggest(ctx, *, idea: str):
    embed = discord.Embed(title="💡 Suggestion",
                          description=idea,
                          color=discord.Color.green())
    embed.set_footer(text=f"Suggested by {ctx.author.display_name}")
    channel = bot.get_channel(SUGGESTION_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
        await ctx.send("✅ Your suggestion was submitted.")
    else:
        await ctx.send("❌ #suggestions channel not found.")


# Start bot
bot.run(TOKEN)
