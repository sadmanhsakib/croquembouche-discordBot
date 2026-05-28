import os, json
import dotenv

dotenv.load_dotenv()

USER_ID = int(os.getenv("USER_ID"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

prefix = None
should_log = None
countdown_channel_id = None
countdown_dict = None

from database import db

async def load_data():
    global prefix, should_log, countdown_channel_id, countdown_dict

    # getting the variable value for the database
    prefix = await db.get_variable("PREFIX")

    should_log = await db.get_variable("SHOULD_LOG")
    should_log = True if should_log.lower() == "true" else False

    countdown_channel_id = await db.get_variable("COUNTDOWN_CHANNEL_ID")
    countdown_channel_id = int(countdown_channel_id)

    countdown_dict = json.loads(await db.get_variable("COUNTDOWN_DATES"))


async def set_default_values():
    await db.set_variable("PREFIX", ".")
    await db.set_variable("COUNTDOWN_CHANNEL_ID", "0")
    await db.set_variable("COUNTDOWN_DATES", '{}')

    print("✅Successfully set the default values!")
