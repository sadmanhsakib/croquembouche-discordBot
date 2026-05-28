import datetime
import discord
import config
from discord.ext import commands
from database import db

# giving the permissions
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.presences = True
intents.members = True

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_prefix(bot, message):
    return config.prefix

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

@bot.event
# when the bot starts
async def on_ready():
    #loading the command script
    await bot.load_extension("bot_commands")
    
    # connecting to the database
    await db.connect()

    try:
        # loading the data from the database
        await config.load_data()
    except Exception:
        # setting the default values
        await config.set_default_values()
        # loading the data from the database
        await config.load_data()

    # prints a message in console when ready
    print(f"✅Logged in as: {bot.user}")


@bot.event
async def on_guild_join(guild):
    # setting the default values
    await config.set_default_values()
    
    # getting the general channel of the server that the BOT just joined
    channel = discord.utils.get(guild.text_channels, name="testing_ground")

    if channel and channel.permissions_for(guild.me).send_messages:
        # sending greeting messages
        await channel.send("Successfully set the default values!")

@bot.event
async def on_message(message):
    # prevents the bot from replying on its own messages
    if message.author == bot.user:
        return

    # processing the commands
    await bot.process_commands(message)


@bot.event
async def on_presence_update(before, after):
    # defining the channels
    countdown_channel_id = config.countdown_channel_id
    countdown_channel = bot.get_channel(countdown_channel_id)

    # defining the timezone
    offset = datetime.timedelta(hours=6)

    # getting the current time
    now = datetime.datetime.now(datetime.timezone(offset, name="GMT +6")).strftime(TIME_FORMAT)

    # checking if it's the user or other members
    if after.id == config.USER_ID:
        old_status = str(before.status)
        new_status = str(after.status)

        # if the user comes online
        if old_status == "offline" and new_status != "offline":
            last_msg_date = ""
            today = now.split(' ')[0]
            
            if config.should_log:
                # updating the database with the current opening time
                await db.set_log(now, "0", "0")

            # getting the last time when a message was send in countdown channel
            async for message in countdown_channel.history(limit=1): 
                # getting the date from the message creation time
                last_msg_date = str(message.created_at + datetime.timedelta(hours=6)).split(' ')[0]

            # if the last countdown reminder wasn't sent on a date
            if last_msg_date != today:
                countdown_counter = 0

                # sends a message for each countdowns
                for key in config.countdown_dict.keys():
                    countdown_counter += 1
                    time_left = time_difference(today, config.countdown_dict[key])
                    await countdown_channel.send(f"{countdown_counter}. {key} : {config.countdown_dict[key]} -> {time_left}")
                    
        elif old_status != "offline" and new_status == "offline" and config.should_log:
            # getting the opening time from the database
            opening_time = await db.get_log()
            active_time = time_difference(opening_time, now)
            
            # updating the database
            await db.set_log(opening_time, now, active_time)
                           

def time_difference(starting, now):
    # if starting contains time too
    if len(starting.split(' ')) == 2:
        # converting the time in datetime
        time1 = datetime.datetime.strptime(starting, TIME_FORMAT)
        time2 = datetime.datetime.strptime(now, TIME_FORMAT)
        active_time = str(time2 - time1)
    else:
        # converting the time in datetime
        time1 = datetime.datetime.strptime(starting, "%Y-%m-%d")
        time2 = datetime.datetime.strptime(now.split(' ')[0], "%Y-%m-%d")
        duration = time2 - time1

        # writing only remaining days as time is unavailable
        active_time = str(duration.days) + " days"

    return active_time


# starts the bot
bot.run(config.BOT_TOKEN)
