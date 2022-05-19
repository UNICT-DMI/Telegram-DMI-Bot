import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message


@pytest.mark.asyncio
async def test_start_cmd(client: TelegramClient):
    """Tests the /start command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(pytest.bot_tag, timeout=pytest.timeout) as conv:
        await conv.send_message("/start")  # send a command
        resp: Message = await conv.get_response()

        assert resp.text.startswith(
            "Welcome! This bot is developed by Computer Science's students to help fellow DMI"
        )
