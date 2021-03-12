"""Tests the bot functionality"""
import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.custom.conversation import Conversation
from module.shared import config_map

TIMEOUT = 8
bot_tag = config_map['test']['tag']


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

        assert resp.text


@pytest.mark.asyncio
async def test_rappresentanti_cmd(client: TelegramClient):
    """Tests the rappresentanti command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        commands = ("/rappresentanti", "/rappresentanti_dmi", "/rappresentanti_informatica", "/rappresentanti_matematica")

        for command in commands:
            await conv.send_message(command)  # send a command
            resp: Message = await conv.get_response()

            assert resp.text


@pytest.mark.asyncio
async def test_help_buttons(client: TelegramClient):
    """Tests all the md buttons in the help command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        buttons = (
            "md_esami_link",
            "md_lezioni_link",
            "md_professori",
            "md_biblioteca",
            "md_gruppi",
            "md_cus",
            "md_cloud",
            "md_sdidattica",
            "md_sstudenti",
            "md_cea",
            "md_ersu",
            "md_ufficioersu",
            "md_urp",
            "md_drive",
            "md_gitlab",
            "md_opismanager",
            "md_contributors",
            "md_help",
            "md_rappresentanti_dmi",
            "md_rappresentanti_informatica",
            "md_rappresentanti_matematica",
        )

        for button in buttons:
            await conv.send_message("/help")  # send a command
            resp: Message = await conv.get_response()

            assert resp.text

            await resp.click(data=button)  # click the inline button
            resp: Message = await conv.get_edit()

            assert resp.text


@pytest.mark.asyncio
async def test_rappresentanti_md_buttons(client: TelegramClient):
    """Tests all the md buttons in the rappresentanti sub-menu

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        buttons = (
            "md_rappresentanti_dmi",
            "md_rappresentanti_informatica",
            "md_rappresentanti_matematica",
        )

        for button in buttons:
            await conv.send_message("/help")  # send a command
            resp: Message = await conv.get_response()

            assert resp.text

            await resp.click(data="sm_rapp_menu")  # click the "👥 Rappresentanti" button
            resp: Message = await conv.get_edit()

            await resp.click(data=button)
            resp: Message = await conv.get_edit()

            assert resp.text
