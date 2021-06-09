"""Tests the bot functionality"""
from datetime import datetime
import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.custom.conversation import Conversation
from module.shared import config_map

TIMEOUT = 8
bot_tag = config_map['test']['tag']


@pytest.mark.asyncio
async def test_start_cmd(client: TelegramClient):
    """Tests the /start command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        await conv.send_message("/start")  # send a command
        resp: Message = await conv.get_response()

        assert resp.text


@pytest.mark.asyncio
async def test_stats_cmd(client: TelegramClient):
    """Tests the /stats and /stats_tot command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        commands = ("/stats", "/stats 3", "/stats_tot")

        for command in commands:
            await conv.send_message(command)  # send a command
            resp: Message = await conv.get_response()

            assert resp.text

            resp: Message = await conv.get_response()

            assert resp.photo


@pytest.mark.asyncio
async def test_rappresentanti_cmd(client: TelegramClient):
    """Tests the /rappresentanti command

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
            "md_studenti",
            "md_cea",
            "md_ersu",
            "md_ufficioersu",
            "md_urp",
            "md_drive",
            "md_gitlab",
            "md_opismanager",
            "md_contributors",
            "md_help",
            "exit_cmd",
        )

        for button in buttons:
            await conv.send_message("/help")  # send a command
            resp: Message = await conv.get_response()

            assert resp.text

            await resp.click(data=button)  # click the inline button
            resp: Message = await conv.get_edit()

            assert resp.text


@pytest.mark.asyncio
async def test_rappresentanti_buttons(client: TelegramClient):
    """Tests all the buttons in the rappresentanti sub-menu

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


@pytest.mark.asyncio
async def test_esami_cmd(client: TelegramClient):
    """Tests all the possible options in the /esami command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:

        await conv.send_message("/esami")  # send a command
        resp: Message = await conv.get_response()

        assert resp.text

        buttons = (
            "sm_esami_button_anno",
            "esami_button_anno_1° anno",
            "sm_esami_button_sessione",
            "esami_button_sessione_prima",
            "sm_esami_button_insegnamento",
        )

        for button in buttons:
            await resp.click(data=button)  # click the button
            resp: Message = await conv.get_edit()

            assert resp.text

        await conv.send_message("ins: programmazione")  # send a message
        resp: Message = await conv.get_response()

        assert resp.text

        await resp.click(data="esami_button_search")  # click the "Cerca" button
        resp: Message = await conv.get_edit()

        assert resp.text


@pytest.mark.asyncio
async def test_lezioni_cmd(client: TelegramClient):
    """Tests all the possible options in the /lezioni command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:

        await conv.send_message("/lezioni")  # send a command
        resp: Message = await conv.get_response()

        assert resp.text

        buttons = (
            "sm_lezioni_button_anno",
            "lezioni_button_anno_1 anno",
            "sm_lezioni_button_giorno",
            "lezioni_button_giorno_1 giorno",
            "sm_lezioni_button_insegnamento",
        )

        for button in buttons:
            await resp.click(data=button)  # click the button
            resp: Message = await conv.get_edit()

            assert resp.text

        await conv.send_message("nome: programmazione")  # send a message
        resp: Message = await conv.get_response()

        assert resp.text

        await resp.click(data="lezioni_button_search")  # click the "Cerca" button
        resp: Message = await conv.get_edit()

        assert resp.text


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

        assert resp.text

        if "⚠️" in resp.text:
            return

        await resp.click(text=f"{datetime.now().day}")  # click the button
        resp: Message = await conv.get_response()

        assert resp.text

        await resp.click(data="sm_aulario")  # click the button
        resp: Message = await conv.get_edit()

        assert resp.text


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

        assert resp.text

        commands = ("/report Test", "/report Test Report")

        for command in commands:
            await conv.send_message(command)  # send a command
            resp: Message = await conv.get_response()

            assert resp.text

            resp: Message = await conv.get_response()

            assert resp.text


@pytest.mark.asyncio
async def test_regolamentodidattico_cmd(client: TelegramClient):
    """Tests the /regolamentodidattico command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        buttons = (
            "reg_button_triennale_L31",
            "reg_button_triennale_L35",
            "reg_button_magistrale_LM18",
            "reg_button_magistrale_LM40",
        )

        for button in buttons:
            await conv.send_message("/regolamentodidattico")  # send a command
            resp: Message = await conv.get_response()

            assert resp.text

            await resp.click(data=button)  # click the button
            resp = await conv.get_edit()

            assert resp.text

            class_num = button.split('_')[-1]
            rule_button_text = "Regolamento Didattico 2020/2021_{}".format(class_num)

            await resp.click(data=rule_button_text)  # click "Regolamento" button

            resp = await conv.get_edit()

            assert resp.text

            resp = await conv.get_response()

            assert resp.document
