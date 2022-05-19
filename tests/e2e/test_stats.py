import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message


@pytest.mark.asyncio
async def test_stats_cmd(client: TelegramClient):
    """Tests the /stats and /stats_tot command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(pytest.bot_tag, timeout=pytest.timeout) as conv:
        commands = ("/stats", "/stats 3", "/stats_tot")

        for command in commands:
            await conv.send_message(command)  # send a command
            resp: Message = await conv.get_response()

            assert resp.text

            resp: Message = await conv.get_response()

            assert resp.photo
