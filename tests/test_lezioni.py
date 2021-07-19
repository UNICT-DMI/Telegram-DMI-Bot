import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message

from . import TIMEOUT, bot_tag


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

        buttons = {
            'sm_lezioni_button_anno': 'Seleziona l\'anno che ti interessa',
            'lezioni_button_anno_1 anno': 'Anno: 1 \nGiorno: tutti\nInsegnamento: tutti',
            'sm_lezioni_button_giorno': 'Seleziona il giorno che ti interessa',
            'lezioni_button_giorno_1 giorno': 'Anno: 1 \nGiorno: LUN\nInsegnamento: tutti',
            'sm_lezioni_button_insegnamento': 'Inserire il nome della materia nel formato:\nnome: nome insegnamento\nEsempio:\nnome: SisTeMi oPeRaTIvI',
        }

        for button, expected_text in buttons.items():
            await resp.click(data=button)  # click the button
            resp: Message = await conv.get_edit()

            assert resp.text == expected_text

        await conv.send_message("nome: programmazione")  # send a message
        resp: Message = await conv.get_response()

        assert resp.text

        await resp.click(data="lezioni_button_search")  # click the "Cerca" button
        resp: Message = await conv.get_edit()

        assert resp.text
