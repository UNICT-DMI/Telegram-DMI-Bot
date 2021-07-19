import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message

from . import TIMEOUT, bot_tag


@pytest.mark.asyncio
async def test_report_cmd(client: TelegramClient):
    """Tests the /report command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:

        await conv.send_message("/report")  # send a command
        resp: Message = await conv.get_response()

        assert (
            resp.text
            == 'Errore. Inserisci la tua segnalazione dopo /report (Ad esempio /report Invasione ingegneri in corso.)'
        )

        commands = ("/report Test", "/report Test Report")

        for command in commands:
            await conv.send_message(command)  # send a command
            resp: Message = await conv.get_response()

            assert resp.text

            resp: Message = await conv.get_response()

            assert resp.text
