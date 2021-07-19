import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message

from . import TIMEOUT, bot_tag


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

        assert resp.text == 'Anno: tutti\nSessione: tutti\nInsegnamento: tutti'

        buttons = {
            'sm_esami_button_anno': 'Seleziona l\'anno che ti interessa',
            'esami_button_anno_1° anno': 'Anno: 1° anno\nSessione: tutti\nInsegnamento: tutti',
            'sm_esami_button_sessione': 'Seleziona la sessione che ti interessa',
            'esami_button_sessione_prima': 'Anno: 1° anno\nSessione: prima\nInsegnamento: tutti',
            'sm_esami_button_insegnamento': 'Inserire l\'insegnamento desiderato nel formato:\nins: nome insegnamento\nEsempio:\nins: SisTeMi oPeRaTIvI',
        }

        for button, expected_test in buttons.items():
            await resp.click(data=button)  # click the button
            resp: Message = await conv.get_edit()

            assert resp.text == expected_test

        await conv.send_message("ins: programmazione")  # send a message
        resp: Message = await conv.get_response()

        assert resp.text

        await resp.click(data="esami_button_search")  # click the "Cerca" button
        resp: Message = await conv.get_edit()

        assert resp.text
