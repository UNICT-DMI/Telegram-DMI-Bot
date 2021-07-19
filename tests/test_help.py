import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message

from . import TIMEOUT, bot_tag


@pytest.mark.asyncio
async def test_help_buttons(client: TelegramClient):
    """Tests all the buttons in the help command

    Args:
        client (TelegramClient): client used to simulate the user
    """

    conv: Conversation
    async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
        buttons = {
            'sm_help_dip_cdl': [
                "md_esami_link",
                "sm_aulario",
                "md_lezioni_link",
                "md_professori",
                "sm_help_rapp_menu",
                "md_biblioteca",
                "md_gruppi",
            ],
            'reg_button_home': [],  # tested by `/regolamentodidattico`
            'sm_help_segr': ["md_sdidattica", "md_studenti", "md_cea"],
            'sm_help_ersu': [
                "md_ersu",
                "md_ufficioersu",
                "md_urp",
            ],
            'sm_help_misc': ["md_drive", "md_gitlab"],
            'sm_help_projects_acknowledgements': [
                "md_opismanager",
                "md_contributors",
            ],
            'md_help': [],
            'exit_cmd': [],
        }

        resp: Message
        for first, nested in buttons.items():
            for button in nested:
                # Open the `help` menu
                await conv.send_message("/help")
                resp = await conv.get_response()
                assert resp.text

                # Click the `first` button
                await resp.click(data=first)
                resp = await conv.get_edit()
                assert resp.text

                # Click the nested element in the menu
                await resp.click(data=button)
                resp = await conv.get_edit()
                assert resp.text
