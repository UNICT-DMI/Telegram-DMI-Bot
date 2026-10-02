import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message


@pytest.mark.asyncio
async def test_lezioni_cmd(client: TelegramClient):
    """Tests all the possible options in the /lezioni command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(pytest.bot_tag, timeout=pytest.timeout) as conv:

        await conv.send_message("/lezioni")  # send a command
        resp: Message = await conv.get_response()
        assert resp.text

        await resp.click(data="lezioni_cdl_LM-18")
        resp = await conv.get_edit()
        assert resp.buttons

        await resp.click(data="lezioni_cur_LM-18_0")
        resp = await conv.get_edit()
        assert resp.text

        await conv.send_message("/lezioni")
        resp = await conv.get_response()
        await resp.click(data="lezioni_cdl_L-31")
        resp = await conv.get_response()
        assert resp.file.mime_type == "application/pdf"
