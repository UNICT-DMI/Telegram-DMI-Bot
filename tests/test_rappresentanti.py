import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message

from . import TIMEOUT, bot_tag


@pytest.mark.asyncio
async def test_rappresentanti_cmd(client: TelegramClient):
    """Tests the /rappresentanti command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        commands = (
            "/rappresentanti",
            "/rappresentanti_dmi",
            "/rappresentanti_informatica",
            "/rappresentanti_matematica",
        )

        for command in commands:
            await conv.send_message(command)  # send a command
            resp: Message = await conv.get_response()

            assert resp.text


@pytest.mark.asyncio
async def test_rappresentanti_buttons(client: TelegramClient):
    """Tests all the buttons in the rappresentanti sub-menu

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        buttons = {
            'md_rappresentanti_dmi': '**Rappresentanti DMI**',
            'md_rappresentanti_informatica': '**Rappresentanti Corso di Laurea Triennale**',
            'md_rappresentanti_matematica': '**Rappresentanti Corso di Laurea Triennale**',
        }

        resp: Message
        for button, expected_text in buttons.items():
            # Open the `rappresentanti` menu into the `/help` menu
            await conv.send_message("/help")
            resp = await conv.get_response()
            assert resp.text

            await resp.click(data="sm_help_dip_cdl")
            resp = await conv.get_edit()
            assert resp.text

            await resp.click(data="sm_help_rapp_menu")
            resp = await conv.get_edit()
            assert resp.text

            await resp.click(data=button)
            resp = await conv.get_edit()

            assert resp.text.startswith(expected_text)
