"""Aulario command"""
import logging
import calendar
from datetime import date
from io import BytesIO
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import CallbackContext
from module.data import TimetableSlot
from module.shared import read_json
from module.data.vars import TEXT_IDS
from module.utils.multi_lang_utils import get_locale

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def aulario(update: Update, context: CallbackContext, chat_id: int = None, message_id: int = None) -> None:
    """Called by the /aulario command.
    Shows the calendar to the user to allow him to select a day from the calendar

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat. Defaults to None.
        message_id: id of the message. Defaults to None.
    """
    if not chat_id:
        chat_id = update.message.chat_id

    days: int = TimetableSlot.get_max_giorno()
    locale: str = update.message.from_user.language_code
    if days:
        reply_markup = create_calendar(days)
        text: str = get_locale(locale, TEXT_IDS.AULARIO_DAY_SELECTION_TEXT_ID)
        if message_id:
            context.bot.editMessageText(text=text, reply_markup=reply_markup, chat_id=chat_id, message_id=message_id)
        else:
            context.bot.sendMessage(text=text, reply_markup=reply_markup, chat_id=chat_id)
    else:
        text: str = get_locale(locale, TEXT_IDS.AULARIO_WARNING_TEXT_ID)
        if message_id:
            context.bot.editMessageText(text=text, chat_id=chat_id, message_id=message_id)
        else:
            context.bot.sendMessage(text=text, chat_id=chat_id)


def month_handler(update: Update, context: CallbackContext) -> None:
    """Called when navigating the calendar of the /aulario command.
    Updates the calendar

    Args:
        update: update event
        context: context passed by the handler
    """
    query: Optional[CallbackQuery] = update.callback_query
    data: Optional[str] = query.data
    chat_id: int = query.message.chat_id
    message_id: int = query.message.message_id

    d: list[str] = data.split("_")
    direction: str = d[1]
    year: int = int(d[2])
    month: int = int(d[3])
    days: int = int(d[4])

    if direction == 'n':
        if month < 12:
            month += 1
        else:
            month = 1
            year += 1
    elif direction == 'p':
        if month > 1:
            month -= 1
        else:
            month = 12
            year -= 1

    context.bot.editMessageReplyMarkup(reply_markup=create_calendar(days, year, month), chat_id=chat_id, message_id=message_id)


def calendar_handler(update: Update, context: CallbackContext) -> None:
    """Called by clicking on a day on the calendar of the /aulario command.
    Show the list of subject for the day

    Args:
        update: update event
        context: context passed by the handler
    """
    query: Optional[CallbackQuery] = update.callback_query
    data: Optional[str] = query.data
    chat_id: int = query.message.chat_id
    locale: str = update.callback_query.from_user.language_code

    day: str = data.split("_")[1]
    daily_slots: list[TimetableSlot] = TimetableSlot.find(giorno=day)
    if daily_slots:
        text = get_locale(locale, TEXT_IDS.AULARIO_LESSON_SELECTION_TEXT_ID)
        keyboard = get_subjs_keyboard(0, day)
        keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_BUTTON_TEXT_TEXT_ID), callback_data='sm_aulario')])
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        text = get_locale(locale, TEXT_IDS.AULARIO_NO_LESSON_WARNING_TEXT_ID)
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_BUTTON_TEXT_TEXT_ID), callback_data='sm_aulario')]])

    context.bot.deleteMessage(chat_id=chat_id, message_id=query.message.message_id)
    context.bot.sendMessage(text=text, reply_markup=reply_markup, chat_id=chat_id)


def subjects_handler(update: Update, context: CallbackContext) -> None:
    """Called when clicking on a subject of the /aulario command.
    Shows more information on the subject selected

    Args:
        update: update event
        context: context passed by the handler
    """
    query: Optional[CallbackQuery] = update.callback_query
    chat_id: int = query.message.chat_id
    locale: str = update.callback_query.from_user.language_code
    ID: str = query.data.split("_")[1]
    slot: TimetableSlot = TimetableSlot.find(ID=ID)[0]

    h: str = f"{slot.ora_inizio} - {slot.end_hour}"
    text: str = f"{slot.nome} {get_locale(locale, TEXT_IDS.AULARIO_LESSON_AT_TIME_TEXT_ID)}: {h}: {slot.aula}"
    photo: Optional[BytesIO] = create_map(slot.nome, h, slot.aula)

    reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup([[InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_BUTTON_TEXT_TEXT_ID), callback_data=f"cal_{slot.giorno}")]])
    context.bot.deleteMessage(chat_id=chat_id, message_id=query.message.message_id)
    if not photo:
        context.bot.sendMessage(text=text, reply_markup=reply_markup, chat_id=chat_id)
    else:
        context.bot.sendPhoto(photo=photo, reply_markup=reply_markup, chat_id=chat_id)


def subjects_arrow_handler(update: Update, context: CallbackContext) -> None:
    """Called when navigating the /aulario menu with the arrows.
    Shows the next or previous page

    Args:
        update: update event
        context: context passed by the handler
    """
    query: Optional[CallbackQuery] = update.callback_query
    data: Optional[str] = query.data
    day: str = data.split('_')[1]
    page: int = int(data.split('_')[2])
    locale: str = update.callback_query.from_user.language_code
    if data[-1] == 'r':
        page += 1
    elif data[-1] == 'l':
        page -= 1

    keyboard = get_subjs_keyboard(page, day)
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_BUTTON_TEXT_TEXT_ID), callback_data='sm_aulario')])

    context.bot.editMessageReplyMarkup(chat_id=query.message.chat_id, message_id=query.message.message_id, reply_markup=InlineKeyboardMarkup(keyboard))


def create_calendar(days: int, year: int = None, month: int = None) -> InlineKeyboardMarkup:
    """Called by :meth:`aulario` and :meth:`month_handler`.
    Creates an InlineKeyboard to append to the message

    Args:
        days: day
        year: yeat. Defaults to None.
        month: month. Defaults to None.

    Returns:
        calendar
    """
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    keyboard = []
    keyboard.append([InlineKeyboardButton(f"🗓 {calendar.month_name[month]} {str(year)}", callback_data="NONE")])
    week = ['L', 'M', 'M', 'G', 'V', 'S', 'D']
    row = []
    for w in week:
        row.append(InlineKeyboardButton(w, callback_data="NONE"))
    keyboard.append(row)
    my_cal = calendar.monthcalendar(year, month)
    diff = 0
    for my_week in my_cal:
        row = []
        empty = True
        for day in my_week:
            if day < today.day and (day == 0 or month == today.month):
                row.append(InlineKeyboardButton(" ", callback_data="NONE"))
            else:
                curr = date(year, month, day)
                diff = (curr - today).days
                if diff < days:
                    empty = False
                    row.append(InlineKeyboardButton(str(day), callback_data=f"cal_{diff}"))
                else:
                    row.append(InlineKeyboardButton(" ", callback_data="NONE"))
        if not empty:
            keyboard.append(row)
    row = []
    if today.month < month or today.year < year:
        row.append(InlineKeyboardButton(f"◀️ {calendar.month_name[((month - 2) % 12) + 1]}", callback_data=f"m_p_{year}_{month}_{days}"))
    if diff < days:
        row.append(InlineKeyboardButton(f"{calendar.month_name[((month) % 12) + 1]} ▶️", callback_data=f"m_n_{year}_{month}_{days}"))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def get_subjs_keyboard(page: int, day: str) -> list:
    """Called by :meth:`calendar_handler` :meth:`subjects_arrow_handler`.
    Generates the keyboard that lists all the subjects for the selected date

    Args:
        page: page of the subject selector
        day: day

    Returns:
        InlineKeyboard
    """
    daily_slots = TimetableSlot.find(giorno=day)
    now_slots = daily_slots
    if day == '0':  # add only the slots that are still to come
        now_slots = [slot for slot in daily_slots if slot.is_still_to_come]

    keyboard = []
    for s in now_slots[page * 5:(page * 5) + 5]:
        keyboard.append([InlineKeyboardButton(s.nome, callback_data=f'sb_{s.ID}')])

    arrows = []
    if page != 0:
        arrows.append(InlineKeyboardButton('◀️', callback_data=f'pg_{day}_{page}_l'))
    if len(now_slots) > page * 5 + 5:
        arrows.append(InlineKeyboardButton('▶️', callback_data=f'pg_{day}_{page}_r'))
    keyboard.append(arrows)
    return keyboard


def create_map(sub: str, h: str, room: str) -> Optional[BytesIO]:
    """Called by :meth:`subjects_handler`.
    Creates an image to show where the lesson will take place.
    Returns None if the hall is not in the base image

    Args:
        sub: name of the subject
        h: time
        room: hall

    Returns:
        photo to send
    """
    data = read_json("room_coordinates")
    if room not in data:
        return None

    b1_path = 'data/img/mappa.jpg'
    b1_img = Image.open(b1_path)
    draw = ImageDraw.Draw(b1_img)
    font = ImageFont.truetype("data/fonts/arial.ttf", 30)
    draw.text((30, 860), f"{sub} Ore: {h} ", fill='black', font=font)
    [x, y, w, z] = data[room]
    draw.rectangle((x, y, w, z), outline='red', width=5)
    bio = BytesIO()
    bio.name = 'image.jpeg'
    b1_img.save(bio, 'JPEG')
    bio.seek(0)
    return bio
