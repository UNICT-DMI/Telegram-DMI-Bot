import pytest
from telethon.sync import TelegramClient
from telethon.tl.custom.conversation import Conversation
from telethon.tl.custom.message import Message


@pytest.mark.asyncio
async def test_regolamentodidattico_cmd(client: TelegramClient):
    """Tests the /regolamentodidattico command

    Args:
        client (TelegramClient): client used to simulate the user
    """
    conv: Conversation
    async with client.conversation(pytest.bot_tag, timeout=pytest.timeout) as conv:
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

            class_num = button.split("_")[-1]
            rule_button_text = "Regolamento Didattico 2020/2021_{}".format(class_num)

            await resp.click(data=rule_button_text)  # click "Regolamento" button

            resp = await conv.get_edit()

            assert resp.text

            resp = await conv.get_response()

            assert resp.document
