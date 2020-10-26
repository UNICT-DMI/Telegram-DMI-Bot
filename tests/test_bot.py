"""Tests the bot functionality"""
import time
import re
import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.custom.conversation import Conversation
from module.shared import config_map, read_md

TIMEOUT = 8
bot_tag = config_map['test']['tag']


def teardown():
    """Makes so that there is a fixed timeout between each test
    """
    time.sleep(1)


def get_telegram_md(message_text: str) -> str:
    """Gets the message received from the bot and reverts it to the Markdowm_v2 used to send messages with it

    Args:
        message_text (str): text of the message received from the bot

    Returns:
        str: the same text of the message, but with the Markdown_v2 conventions
    """
    message_text = re.sub(r"(?<=[^_])_(?=[^_])", r"\_", message_text)  # _ -> \_
    return message_text.replace("__", "_").replace("**", "*") # __ -> _ | ** -> *


@pytest.mark.asyncio
async def test_start_cmd(client: TelegramClient):
    """Tests the start command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        await conv.send_message("/start")  # send a command
        resp: Message = await conv.get_response()

        assert read_md("start") == get_telegram_md(resp.text)


@pytest.mark.asyncio
async def test_rappresentanti_cmd(client: TelegramClient):
    """Tests the rappresentanti command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        await conv.send_message("/rappresentanti")  # send a command
        resp: Message = await conv.get_response()
        print(read_md("rappresentanti"))
        print(get_telegram_md(resp.text))
        assert read_md("rappresentanti") == get_telegram_md(resp.text)


# TODO: to be completed
@pytest.mark.asyncio
async def test_help_cmd(client: TelegramClient):
    """Tests the rappresentanti command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        await conv.send_message("/help")  # send a command
        resp: Message = await conv.get_response()

        assert "@DMI_Bot risponde ai seguenti comandi:" == resp.text

        await resp.click(text="📖 Esami (link)") # click "📖 Esami (link)" inline button
        resp: Message = await conv.get_edit()

        assert read_md("esami_link") == get_telegram_md(resp.text)

# SEGUE QUALCHE ESEMPIO PRESO DA UN ALTRO BOT

# @pytest.mark.asyncio
# async def test_settings_cmd(client: TelegramClient):
#     """Tests the settings command

#     Args:
#         client (TelegramClient): client used to simulate the user
#     """
#     config_map['image']['blur'] = config_map['image']['font_size_title'] = config_map['image']['font_size_caption'] = 30
#     conv: Conversation
#     async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#         for button_index in (1, 2, 3):
#             await conv.send_message("/settings")  # send a command
#             resp: Message = await conv.get_response()

#             assert read_md("settings") == get_telegram_md(resp.text)

#             # click inline keyboard (Sfocatura, Dimensioni testo, Caratteri per linea)
#             await resp.click(button_index)
#             resp: Message = await conv.get_edit()

#             assert read_md("settings") == get_telegram_md(resp.text)

#             await resp.click(text="➕")  # click inline keyboard (➕)
#             resp: Message = await conv.get_edit()

#             assert read_md("settings") == get_telegram_md(resp.text)

#             await resp.click(text="➖")  # click inline keyboard (➖)
#             resp: Message = await conv.get_edit()

#             assert read_md("settings") == get_telegram_md(resp.text)

#             await resp.click(text="Chiudi")  # click inline keyboard (Chiudi)
#             resp: Message = await conv.get_edit()

#         assert 30 == config_map['image']['blur'] == config_map['image'][
#             'font_size_title'] == config_map['image']['font_size_caption']


# @pytest.mark.asyncio
# async def test_cancel_cmd(client: TelegramClient):
#     """Tests the cancel command

#     Args:
#         client (TelegramClient): client used to simulate the user
#     """
#     conv: Conversation
#     async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#         await conv.send_message("/create")  # send a command
#         resp: Message = await conv.get_response()
#         await conv.send_message("/cancel")  # send a command
#         resp: Message = await conv.get_response()

#         assert read_md("cancel") == get_telegram_md(resp.text)


# @pytest.mark.asyncio
# async def test_templates_conversation(client: TelegramClient):
#     """Tests the selection of all the possible templates in the create conversation

#     Args:
#         client (TelegramClient): client used to simulate the user
#     """
#     conv: Conversation
#     async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#         for template in ('DMI', 'DMI vuoto', 'Informatica', 'Informatica vuoto', 'Matematica', 'Matematica vuoto'):
#             await conv.send_message("/create")  # send a command
#             resp: Message = await conv.get_response()
#             # click inline keyboard (Vuoto, DMI, Informatica, Matematica)
#             await resp.click(text=template)
#             resp: Message = await conv.get_edit()

#             assert read_md("template") == get_telegram_md(resp.text)

#             await conv.send_message("/cancel")  # send a command
#             resp: Message = await conv.get_response()

#             assert read_md("cancel") == get_telegram_md(resp.text)


# @pytest.mark.asyncio
# async def test_fail_conversation(client: TelegramClient):
#     """Tests the create conversation when the user inputs some invalid text when asked for the image

#     Args:
#         client (TelegramClient): client used to simulate the user
#     """
#     conv: Conversation
#     async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#         await conv.send_message("/create")  # send a command
#         resp: Message = await conv.get_response()
#         await resp.click(text="DMI")  # click inline keyboard
#         resp: Message = await conv.get_edit()
#         await conv.send_message("Test titolo")  # send a message
#         resp: Message = await conv.get_response()
#         await conv.send_message("Test descrizione")  # send a message
#         resp: Message = await conv.get_response()
#         await resp.click(text="Ridimensiona")  # click inline keyboard
#         resp: Message = await conv.get_edit()
#         await conv.send_message("Fail message")  # send a message
#         resp: Message = await conv.get_response()

#         assert read_md("fail") == get_telegram_md(resp.text)

#         await conv.send_message("/cancel")  # send a command
#         resp: Message = await conv.get_response()

#         assert read_md("cancel") == get_telegram_md(resp.text)


# @pytest.mark.asyncio
# async def test_create_scale_conversation(client: TelegramClient):
#     """Tests the whole flow of the create conversation with the default image
#     The image creation is handled by the main thread

#     Args:
#         client (TelegramClient): client used to simulate the user
#     """
#     config_map['image']['thread'] = False
#     conv: Conversation
#     async with client.conversation(bot_tag, timeout=TIMEOUT * 2) as conv:
#         await conv.send_message("/create")  # send a command
#         resp: Message = await conv.get_response()

#         assert read_md("create") == get_telegram_md(resp.text)

#         await resp.click(text="DMI")  # click inline keyboard
#         resp: Message = await conv.get_edit()

#         assert read_md("template") == get_telegram_md(resp.text)

#         await conv.send_message("Test titolo")  # send a message
#         resp: Message = await conv.get_response()

#         assert read_md("title") == get_telegram_md(resp.text)

#         await conv.send_message("Test descrizione")  # send message
#         resp: Message = await conv.get_response()

#         assert read_md("caption") == get_telegram_md(resp.text)

#         await resp.click(text="Ridimensiona")  # click inline keyboard
#         resp: Message = await conv.get_edit()

#         await conv.send_file("data/img/bg_test.png")  # send message
#         resp: Message = await conv.get_response()

#         assert read_md("background") == get_telegram_md(resp.text)

#         resp: Message = await conv.get_response()

#         assert resp.photo is not None
