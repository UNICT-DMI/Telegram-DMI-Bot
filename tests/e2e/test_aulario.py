import calendar
from datetime import datetime

import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message


@pytest.mark.asyncio
async def test_aulario_cmd(client: TelegramClient):
    """Tests the /aulario command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(pytest.bot_tag, timeout=pytest.timeout) as conv:

        await conv.send_message("/aulario")  # send a command
        resp: Message = await conv.get_response()

        if "⚠️" in resp.text:
            return

        assert resp.text == 'Seleziona la data della lezione che ti interessa.'

        now = datetime.now()

        await resp.click(text=f"{now.day}")  # click the button
        resp: Message = await conv.get_response()
        assert resp.text

        await resp.click(data="sm_aulario")  # click the button
        resp = await conv.get_edit()
        assert resp.text

        await resp.click(
            text="{} ▶️".format(calendar.month_name[((now.month % 12) + 1)])
        )
        resp = await conv.get_edit()
        assert resp.text

        await resp.click(
            text="{} ▶️".format(calendar.month_name[((now.month % 12) + 2)])
        )
        resp = await conv.get_edit()
        assert resp.text

        await resp.click(
            text="◀️ {}".format(calendar.month_name[((now.month % 12) + 1)])
        )
        resp = await conv.get_edit()
        assert resp.text
