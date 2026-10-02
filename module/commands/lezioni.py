# -*- coding: utf-8 -*-
"""/lezioni command"""

import html
import logging
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from module.data.vars import PLACE_HOLDER, TEXT_IDS
from module.shared import check_log, read_md
from module.utils.multi_lang_utils import get_locale

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_course_urls() -> Dict[str, str]:
    """Reads the timetable page of each course from the lezioni_link markdown file

    Returns:
        course code (e.g. L-31) -> url of its timetable page
    """
    urls = {}
    for line in read_md("lezioni_link").splitlines():
        code, _, url = line.partition(":")
        if url:
            urls[code.strip()] = url.strip()
    return urls


def get_course_page(url: str) -> Optional[BeautifulSoup]:
    """Downloads the main content of a course page

    Args:
        url: url of the page

    Returns:
        content of the page, or None if it could not be downloaded
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("Could not download `%s`", url)
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.find(id="content") or soup


def parse_timetable(page: BeautifulSoup) -> Dict[str, str]:
    """Parses the timetable tables of a course page, as published by LM-18.
    Each table starts with a single-cell header like "CURRICULUM HEALTH INFORMATICS - Primo Anno",
    followed by rows of subject, days, time and room; a row without subject continues the one above.

    Args:
        page: content of the course page

    Returns:
        curriculum -> its timetable, formatted as Telegram HTML
    """
    timetable: Dict[str, str] = {}
    for table in page.find_all("table"):
        rows = [
            [
                " ".join(cell.get_text(" ").split())
                for cell in row.find_all(["td", "th"])
            ]
            for row in table.find_all("tr")
        ]
        if not rows or len(rows[0]) != 1:
            continue
        header = re.sub(r"^CURRICULUM\s+", "", rows[0][0], flags=re.IGNORECASE)
        curriculum, _, year = header.partition(" - ")
        text = f"\n<b>{html.escape(year or curriculum)}</b>\n"
        for cells in rows[1:]:
            if len(cells) != 4:
                continue
            subject, days, hours, room = (html.escape(cell) for cell in cells)
            if subject:
                text += f"{subject}\n"
            text += f"    {days}, {hours}, {room}\n"
        timetable[curriculum] = timetable.get(curriculum, "") + text
    return timetable


def find_timetable_pdfs(page: BeautifulSoup, page_url: str) -> List[str]:
    """Finds the timetable PDFs of a course page.
    PDFs embedded in a viewer come first, as the attached ones may be from past semesters (e.g. LM-40).

    Args:
        page: content of the course page
        page_url: url of the course page

    Returns:
        urls of the PDFs
    """
    embedded = [
        parse_qs(urlparse(iframe["src"]).query).get("file", [""])[0]
        for iframe in page.find_all("iframe", src=True)
    ]
    pdfs = [urljoin(page_url, pdf) for pdf in embedded if pdf]
    if pdfs:
        return pdfs
    return [
        urljoin(page_url, a["href"])
        for a in page.find_all(
            "a", href=True, attrs={"type": re.compile(r"^application/pdf")}
        )
    ]


def get_courses_keyboard() -> InlineKeyboardMarkup:
    """Generates the keyboard to choose the course of the /lezioni command

    Returns:
        InlineKeyboard
    """
    buttons = [
        InlineKeyboardButton(code, callback_data=f"lezioni_cdl_{code}")
        for code in get_course_urls()
    ]
    return InlineKeyboardMarkup([buttons[i : i + 2] for i in range(0, len(buttons), 2)])


def lezioni(update: Update, context: CallbackContext) -> None:
    """Called by the /lezioni command.
    Shows the courses to the user, to choose the one whose timetable to see

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "lezioni")

    user_id: int = update.message.from_user.id
    chat_id: int = update.message.chat_id
    locale: str = update.message.from_user.language_code

    if (
        chat_id != user_id
    ):  # forza ad eseguire il comando in una chat privata, anche per evitare di inondare un gruppo con i risultati
        context.bot.sendMessage(
            chat_id=chat_id,
            text=get_locale(locale, TEXT_IDS.USE_WARNING_TEXT_ID).replace(
                PLACE_HOLDER, "/lezioni"
            ),
        )
        context.bot.sendMessage(
            chat_id=user_id,
            text=get_locale(locale, TEXT_IDS.GROUP_WARNING_TEXT_ID).replace(
                PLACE_HOLDER, "/lezioni"
            ),
        )

    context.bot.sendMessage(
        chat_id=chat_id,
        text=get_locale(locale, TEXT_IDS.CLASSES_SELECT_COURSE_TEXT_ID),
        reply_markup=get_courses_keyboard(),
    )


def lezioni_courses_handler(update: Update, _: CallbackContext) -> None:
    """Called by the back button of the /lezioni curricula.
    Shows the courses again

    Args:
        update: update event
        context: context passed by the handler
    """
    query: CallbackQuery = update.callback_query
    query.edit_message_text(
        text=get_locale(
            query.from_user.language_code, TEXT_IDS.CLASSES_SELECT_COURSE_TEXT_ID
        ),
        reply_markup=get_courses_keyboard(),
    )


def lezioni_course_handler(update: Update, context: CallbackContext) -> None:
    """Called by clicking on a course of the /lezioni command.
    Shows its curricula if the course page has a timetable, otherwise sends its PDFs

    Args:
        update: update event
        context: context passed by the handler
    """
    query: CallbackQuery = update.callback_query
    locale: str = query.from_user.language_code
    code: str = query.data.replace("lezioni_cdl_", "")
    url: str = get_course_urls().get(code, "")
    page = get_course_page(url) if url else None
    timetable = parse_timetable(page) if page else {}

    if timetable:
        keyboard = [
            [InlineKeyboardButton(curriculum, callback_data=f"lezioni_cur_{code}_{i}")]
            for i, curriculum in enumerate(timetable)
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    get_locale(locale, TEXT_IDS.BACK_BUTTON_TEXT_TEXT_ID),
                    callback_data="lezioni_home",
                )
            ]
        )
        query.edit_message_text(
            text=get_locale(locale, TEXT_IDS.CLASSES_SELECT_CURRICULUM_TEXT_ID),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    pdfs = find_timetable_pdfs(page, url) if page else []
    if not pdfs:
        query.edit_message_text(
            text=get_locale(locale, TEXT_IDS.CLASSES_UNAVAILABLE_TEXT_ID).replace(
                PLACE_HOLDER, url
            )
        )
        return

    query.edit_message_text(
        text=get_locale(locale, TEXT_IDS.CLASSES_TIMETABLE_TEXT_ID).replace(
            PLACE_HOLDER, code
        )
    )
    for pdf in pdfs:
        try:
            context.bot.send_document(chat_id=query.message.chat_id, document=pdf)
        except BadRequest:
            logger.exception("Telegram could not send `%s`", pdf)
            context.bot.sendMessage(chat_id=query.message.chat_id, text=pdf)


def lezioni_curriculum_handler(update: Update, _: CallbackContext) -> None:
    """Called by clicking on a curriculum of the /lezioni command.
    Shows its timetable

    Args:
        update: update event
        context: context passed by the handler
    """
    query: CallbackQuery = update.callback_query
    locale: str = query.from_user.language_code
    code, index = query.data.replace("lezioni_cur_", "").rsplit("_", 1)
    url: str = get_course_urls().get(code, "")
    page = get_course_page(url) if url else None
    curricula: List[Tuple[str, str]] = (
        list(parse_timetable(page).items()) if page else []
    )

    if int(index) >= len(curricula):
        query.edit_message_text(
            text=get_locale(locale, TEXT_IDS.CLASSES_UNAVAILABLE_TEXT_ID).replace(
                PLACE_HOLDER, url
            )
        )
        return

    curriculum, timetable = curricula[int(index)]
    query.edit_message_text(
        text=f"<b>{html.escape(curriculum)}</b>\n{timetable}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        get_locale(locale, TEXT_IDS.BACK_BUTTON_TEXT_TEXT_ID),
                        callback_data=f"lezioni_cdl_{code}",
                    )
                ]
            ]
        ),
    )
