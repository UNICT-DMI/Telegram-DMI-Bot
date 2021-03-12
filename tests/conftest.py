"""Test configuration"""
import asyncio
import warnings
import pytest
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telegram.ext import Updater
from main import add_handlers, add_jobs
from module.shared import config_map

warnings.filterwarnings("ignore",
                        message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked for every message.")

api_id = config_map['test']['api_id']
api_hash = config_map['test']['api_hash']
session = config_map['test']['session']


def get_session():
    """Shows the String session.
    The string found must be inserted in the settings.yaml file
    """
    with TelegramClient(StringSession(), api_id, api_hash) as connection:
        print("Your session string is:", connection.session.save())


@pytest.fixture(scope="session")
def event_loop():
    """Allows to use @pytest.fixture(scope="session") for the folowing functions

    Yields:
        AbstractEventLoop: loop to be executed
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def bot():
    """Called at the beginning of the testing session.
    Starts the bot with the testing setting in another thread

    Yields:
        None: wait for the testing session to end
    """
    print("[info] started telegram bot")
    config_map['token'] = config_map['test']['token']
    updater = Updater(config_map['token'], request_kwargs={'read_timeout': 20, 'connect_timeout': 20}, use_context=True)
    add_handlers(updater.dispatcher)
    add_jobs(updater.job_queue)
    updater.start_polling()
    await asyncio.sleep(2)

    yield None

    updater.stop()
    print("[info] closed telegram bot")


@pytest.fixture(scope="session")
async def client() -> TelegramClient:
    """Called at the beginning of the testing session.
    Creates the telegram client that will simulate the user

    Yields:
        Iterator[TelegramClient]: telegram client that will simulate the user
    """
    print("[info] started telegram client")
    tg_client = TelegramClient(StringSession(session), api_id, api_hash, sequential_updates=True)

    await tg_client.connect()  # Connect to the server
    await tg_client.get_me()  # Issue a high level command to start receiving message
    await tg_client.get_dialogs()  # Fill the entity cache

    yield tg_client

    await tg_client.disconnect()
    await tg_client.disconnected

    print("[info] closed telegram client")


if __name__ == "__main__":
    get_session()
