import calendar
from datetime import datetime

import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message

from . import TIMEOUT, bot_tag


@pytest.mark.asyncio
async def test_aulario_cmd(client: TelegramClient):
    """Tests the /aulario command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:

        await conv.send_message("/aulario")  # send a command
        resp: Message = await conv.get_response()

        assert resp.text == 'Seleziona la data della lezione che ti interessa.'

        if "⚠️" in resp.text:
            return

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
