# -*- coding: utf-8 -*-
"""Test suite for the /lezioni command."""

from unittest.mock import MagicMock, patch

import requests
from bs4 import BeautifulSoup
from telegram import ParseMode

from module.commands.lezioni import (
    find_timetable_pdfs,
    get_course_urls,
    lezioni_course_handler,
    lezioni_curriculum_handler,
    parse_timetable,
)

LM18_HTML = """
<div id="content">
  <table>
    <tr><td colspan="4">CURRICULUM ARTIFICIAL INTELLIGENCE - Primo Anno</td></tr>
    <tr><td>Algoritmi e complessità</td><td>lunedì e mercoledì</td><td>08:00-11:00</td><td>Aula 25</td></tr>
  </table>
  <table>
    <tr><td colspan="4">CURRICULUM ARTIFICIAL INTELLIGENCE - Secondo Anno</td></tr>
    <tr><td>Software Quality &amp; Project Development</td><td>mercoledì</td><td>08:00-10:00</td><td>Aula 24</td></tr>
    <tr><td></td><td>venerdì</td><td>15:00-19:00</td><td>Aula F</td></tr>
  </table>
  <table>
    <tr><td colspan="4">CURRICULUM HEALTH INFORMATICS - Primo Anno</td></tr>
    <tr><td>Bioinformatics Foundations</td><td>martedì</td><td>17:00-19:00</td><td>Aula 36</td></tr>
  </table>
</div>
"""

L31_HTML = """
<div id="content">
  <a href="https://web.dmi.unict.it/sites/default/files/1anno.pdf" type="application/pdf; length=1">1anno.pdf</a>
  <a href="/sites/default/files/2anno.pdf" type="application/pdf; length=1">2anno.pdf</a>
  <a href="/avvisi">Avvisi</a>
</div>
"""

LM40_HTML = """
<div id="content">
  <iframe class="pdf" src="/sites/all/libraries/pdf.js/web/viewer.html?file=https%3A%2F%2Fweb.dmi.unict.it%2Fsites%2Fdefault%2Ffiles%2FORARIO%2520LM40%2520I%2520sem.pdf"></iframe>
  <a href="https://web.dmi.unict.it/sites/default/files/Orario_LM-40_II.pdf" type="application/pdf; length=1">Orario II semestre</a>
</div>
"""

LM18_URL = "http://web.dmi.unict.it/corsi/lm-18/orario-delle-lezioni"
L31_URL = "https://web.dmi.unict.it/corsi/l-31/orario-delle-lezioni"


def page(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser").find(id="content")


def callback_update(data: str) -> MagicMock:
    update = MagicMock()
    update.callback_query.data = data
    update.callback_query.from_user.language_code = "it"
    return update


def keyboard_callbacks(markup) -> list:
    return [b.callback_data for row in markup.inline_keyboard for b in row]


def test_get_course_urls() -> None:
    urls = get_course_urls()

    assert list(urls) == ["L-31", "L-35", "LM-18", "LM-40"]
    assert urls["L-31"] == L31_URL
    assert urls["LM-18"] == LM18_URL


def test_parse_timetable_groups_years_by_curriculum() -> None:
    assert parse_timetable(page(LM18_HTML)) == {
        "ARTIFICIAL INTELLIGENCE": (
            "\n<b>Primo Anno</b>\n"
            "Algoritmi e complessità\n"
            "    lunedì e mercoledì, 08:00-11:00, Aula 25\n"
            "\n<b>Secondo Anno</b>\n"
            "Software Quality &amp; Project Development\n"
            "    mercoledì, 08:00-10:00, Aula 24\n"
            "    venerdì, 15:00-19:00, Aula F\n"
        ),
        "HEALTH INFORMATICS": (
            "\n<b>Primo Anno</b>\n"
            "Bioinformatics Foundations\n"
            "    martedì, 17:00-19:00, Aula 36\n"
        ),
    }


def test_parse_timetable_ignores_pages_without_timetable() -> None:
    assert not parse_timetable(page(L31_HTML))


def test_find_timetable_pdfs_prefers_the_embedded_viewer() -> None:
    assert find_timetable_pdfs(page(LM40_HTML), "https://web.dmi.unict.it/x") == [
        "https://web.dmi.unict.it/sites/default/files/ORARIO%20LM40%20I%20sem.pdf"
    ]


def test_find_timetable_pdfs_falls_back_to_the_attachments() -> None:
    assert find_timetable_pdfs(page(L31_HTML), L31_URL) == [
        "https://web.dmi.unict.it/sites/default/files/1anno.pdf",
        "https://web.dmi.unict.it/sites/default/files/2anno.pdf",
    ]


@patch('module.commands.lezioni.requests.get')
def test_course_handler_shows_the_curricula(mock_get) -> None:
    mock_get.return_value = MagicMock(text=LM18_HTML)
    update = callback_update("lezioni_cdl_LM-18")

    lezioni_course_handler(update, MagicMock())

    mock_get.assert_called_once_with(LM18_URL, timeout=10)
    markup = update.callback_query.edit_message_text.call_args.kwargs["reply_markup"]
    assert keyboard_callbacks(markup) == [
        "lezioni_cur_LM-18_0",
        "lezioni_cur_LM-18_1",
        "lezioni_home",
    ]


@patch('module.commands.lezioni.requests.get')
def test_course_handler_sends_the_pdfs(mock_get) -> None:
    mock_get.return_value = MagicMock(text=L31_HTML)
    update = callback_update("lezioni_cdl_L-31")
    context = MagicMock()

    lezioni_course_handler(update, context)

    assert [c.kwargs["document"] for c in context.bot.send_document.call_args_list] == [
        "https://web.dmi.unict.it/sites/default/files/1anno.pdf",
        "https://web.dmi.unict.it/sites/default/files/2anno.pdf",
    ]


@patch('module.commands.lezioni.requests.get')
def test_course_handler_links_the_page_when_the_site_is_down(mock_get) -> None:
    mock_get.side_effect = requests.ConnectionError()
    update = callback_update("lezioni_cdl_L-31")
    context = MagicMock()

    lezioni_course_handler(update, context)

    assert L31_URL in update.callback_query.edit_message_text.call_args.kwargs["text"]
    context.bot.send_document.assert_not_called()


@patch('module.commands.lezioni.requests.get')
def test_curriculum_handler_shows_the_timetable(mock_get) -> None:
    mock_get.return_value = MagicMock(text=LM18_HTML)
    update = callback_update("lezioni_cur_LM-18_1")

    lezioni_curriculum_handler(update, MagicMock())

    kwargs = update.callback_query.edit_message_text.call_args.kwargs
    assert kwargs["text"] == (
        "<b>HEALTH INFORMATICS</b>\n"
        "\n<b>Primo Anno</b>\n"
        "Bioinformatics Foundations\n"
        "    martedì, 17:00-19:00, Aula 36\n"
    )
    assert kwargs["parse_mode"] == ParseMode.HTML
    assert keyboard_callbacks(kwargs["reply_markup"]) == ["lezioni_cdl_LM-18"]
