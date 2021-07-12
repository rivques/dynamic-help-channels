# bot.py
import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv # pyright: reportMissingImports=false
from dataclasses import dataclass
from typing import Optional

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#The background is set with 40 plus the number of the color, and the foreground with 30

#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

def formatter_message(message, use_color = True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message

COLORS = {
    'WARNING': CYAN,
    'INFO': GREEN,
    'DEBUG': WHITE,
    'CRITICAL': RED,
    'ERROR': YELLOW
}

class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color = True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = "\033[38;2;30;30;30m" + COLOR_SEQ % (40 + COLORS[levelname]) + "[" + levelname + "]" + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(levelname)s: %(message)s'))
logger.addHandler(handler)

channel_names = ['apple', 'strawberry', 'pepper', 'criossant', 'pancake', 'pizza', 'taco', 'pasta', 'ice-cream', 'pie', 'cupcake', 'chocolate', 'cake', 'cookie', 'donut', 'popcorn', 'bagel', 'broccoli', 'bread', 'potato', 'carrot', 'coconut', 'pineapple', 'mango']

@dataclass
class RegisteredGuild:
    guild: discord.Guild
    active_category: Optional[discord.CategoryChannel]
    ready_category: Optional[discord.CategoryChannel]
    dormant_category: Optional[discord.CategoryChannel]

bot = commands.Bot(command_prefix='$')

bot.registered_guilds = {}

@bot.command(name="solved")
async def solved(ctx):
    pass

@bot.command(name="ping")
async def ping(ctx):
    logger.debug("Pinged!")
    await ctx.channel.send("Pong!")

@bot.command(name="setup")
@commands.has_guild_permissions(administrator=True)
async def setup(ctx: commands.Context):
    await ctx.send("Welcome to Dynamic Help Channels! You have begun setup. I will ask you a series of questions to help set up the bot.")
    await ctx.send("You will need 3 channel categories: one for active help channels, one for available help channels, and one for dormant help channels.")
    await ctx.send("You will also need to have the Discord IDs of those categories. For more on that, see https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-")
    await ctx.send("Please type the ID -- and nothing but the ID -- of the category you would like to hold **active** help channels.")
    # Get the RegisteredGuild the message was sent in
    try:
        registered_guild: RegisteredGuild = bot.registered_guilds[ctx.guild.id]
    except KeyError:
        # how did we get here
        # do nothing and hope nothing breaks
        await ctx.send("Something is very wrong with the bot. I have no idea how it has reached this point. Sorry! Maybe try kicking the bot and reinviting it?")
        return
    def check(m):
        return ((m.channel.id == ctx.channel.id) and (m.author.id == ctx.message.author.id))
    while True:
        reply = await bot.wait_for('message', check=check)
        try: 
            reply = int(reply.content)
        except ValueError:
            logger.debug("value error, invalid")
            await ctx.send("That was not a valid ID! Please try again!")
            continue


        for pos_category in ctx.guild.categories:
            if pos_category.id == reply:
                registered_guild.active_category = pos_category
                break
        else:
            await ctx.send("That category does not exist in this server! Please try again!")
            continue
        break

    await ctx.send(f'Selected "{registered_guild.active_category.name}" as the category for **active** help channels. Now please type the ID of the category for **available** help channels.')
    while True:
        reply = await bot.wait_for('message', check=check)
        try: 
            reply = int(reply.content)
        except ValueError:
            logger.debug("value error, invalid")
            await ctx.send("That was not a valid ID! Please try again!")
            continue


        for pos_category in ctx.guild.categories:
            if pos_category.id == reply:
                registered_guild.available_category = pos_category
                break
        else:
            await ctx.send("That category does not exist in this server! Please try again!")
            continue
        break

    await ctx.send(f'Selected "{registered_guild.available_category.name}" as the category for **available** help channels. Now please type the ID of the category for **dormant** help channels.')
    while True:
        reply = await bot.wait_for('message', check=check)
        try: 
            reply = int(reply.content)
        except ValueError:
            logger.debug("value error, invalid")
            await ctx.send("That was not a valid ID! Please try again!")
            continue


        for pos_category in ctx.guild.categories:
            if pos_category.id == reply:
                registered_guild.dormant_category = pos_category
                break
        else:
            await ctx.send("That category does not exist in this server! Please try again!")
            continue
        break
    await ctx.send(f'Selected "{registered_guild.dormant_category.name}" as the category for **dormant** help channels.')
    await ctx.send('Would you like for me to automatically create channels in those categories? (y/n)')
    while True:
        reply = await bot.wait_for('message', check=check)
        if reply.content.lower() in ['y', 'yes', 'yep']:
            await ctx.send("Okay! Making channels...")
            for channel_name in channel_names:
                await registered_guild.dormant_category.create_text_channel("help-" + channel_name)
            await ctx.send("Now active...")
            break
        elif reply.content.lower() in ['n', 'no', 'nope']:
            await ctx.send("Okay! Now active...")
            break
        else:
            await ctx.send("That was not a valid answer! Please try again!")

@bot.event
async def on_message(message: discord.Message):
    await bot.process_commands(message)
    # Get the RegisteredGuild the message was sent in
    try:
        registered_guild: RegisteredGuild = bot.registered_guilds[message.guild.id]
    except KeyError:
        # how did we get here
        # do nothing and hope nothing breaks
        return
    if None in [registered_guild.active_category, registered_guild.ready_category, registered_guild.dormant_category]:
        # The bot isn't fully configured, return
        return
    # Make sure we aren't respponding to our own message
    if message.author == bot.user:
        return
    if message.channel.category_id == registered_guild.ready_category.id:
        # Someone needs help!
        # Move the channel to the active category
        await message.channel.move(category=registered_guild.active_category)
        # pin the message
        await message.pin()
    


@bot.event
async def on_ready():
    for guild in bot.guilds:
        # register each guild the bot is a part of
        logger.debug("registering guild " + guild.name)
        registered_guild = RegisteredGuild(guild=guild, active_category=None, ready_category=None, dormant_category=None)
        bot.registered_guilds[guild.id] = registered_guild
    
    logger.info("Up and running!")

@bot.event
async def on_join_guild(guild):
    # register the new guild and say hello
    logger.debug("registering guild " + guild.name)
    registered_guild = RegisteredGuild(guild=guild, active_category=None, ready_category=None, dormant_category=None)
    bot.registered_guilds[guild.id] = registered_guild

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.MissingPermissions):
        await ctx.send('You do need to be an administrator this command.')
    else:
        raise error

bot.run(TOKEN)