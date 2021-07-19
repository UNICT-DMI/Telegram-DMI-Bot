from time import sleep

import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message

from . import TIMEOUT, bot_tag


@pytest.mark.asyncio
async def test_prof_cmd(client: TelegramClient):
    """Tests the /prof command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        commands = (
            "/prof",
            "/prof bilotta",
            "/prof giuseppe bilotta",
            "/prof rocco senteta",
            "/prof Dario",
            "/prof a",
        )

        for command in commands:
            await conv.send_message(command)  # send a command
            resp: Message = await conv.get_response()

            assert resp.text

            sleep(2)
