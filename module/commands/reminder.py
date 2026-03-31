# -*- coding: utf-8 -*-
"""/esami command"""

import ast
import logging
import re
from datetime import date, datetime
from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from module.data import Exam
from module.data.db_manager import DbManager
from module.data.reminder import ExamRegistration
from module.data.vars import PLACE_HOLDER, TEXT_IDS
from module.shared import check_log
from module.utils.multi_lang_utils import get_locale

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def reminder(update: Update, context: CallbackContext) -> None:
    """Called by the /reminder command.
    Sets a reimnder to sign up for a certain exam date.

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "reminder")

    if (
        'reminder' in context.user_data
    ):  # ripulisce il dict dell'user relativo a /reminder da eventuali dati presenti
        context.user_data['reminder'].clear()
    else:  # crea il dict che conterrà i dati del comando /reminder all'interno della key ['reminder'] di user data
        context.user_data['reminder'] = {}

    user_id: int = update.message.from_user.id
    chat_id: int = update.message.chat_id
    locale: str = update.message.from_user.language_code
    if chat_id != user_id:  # forza ad eseguire il comando in una chat privata
        context.bot.sendMessage(
            chat_id=chat_id,
            text=get_locale(locale, TEXT_IDS.USE_WARNING_TEXT_ID).replace(
                PLACE_HOLDER, "/reminder"
            ),
        )
        context.bot.sendMessage(
            chat_id=user_id,
            text=get_locale(locale, TEXT_IDS.GROUP_WARNING_TEXT_ID).replace(
                PLACE_HOLDER, "/reminder"
            ),
        )

    message_text: str = get_locale(locale, TEXT_IDS.REMINDER_FIRST_SELECTION)

    keyboard: List[List[InlineKeyboardButton]] = [[]]
    keyboard = [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.REMINDER_ADD),
                callback_data="rem_add",
            ),
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.REMINDER_DELETE),
                callback_data="rem_del",
            ),
        ]
    ]

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def reminder_send_message(
    reminders: list,
    context: CallbackContext,
    first_target_date: str,
    second_target_date: str,
) -> None:
    '''Sends a message to the user to remind them to register for the exam.'''

    for rem in reminders:
        student_id = rem.get('studenti')
        subject = rem.get('insegnamento', 'N/D')
        prof = rem.get('docenti', 'N/D')
        exam_date = rem.get('data')
        locale = rem.get('lingua', 'it')

        # sceglie se mandare il primo o il secondo reminder in base a se mancano 14 o 4 giorni dall'esame
        if exam_date == first_target_date:
            message_text: str = (
                get_locale(locale, TEXT_IDS.REMINDER_FIRST_MESSAGE)
                .replace(PLACE_HOLDER, subject, 1)
                .replace(PLACE_HOLDER, prof, 1)
                .replace(PLACE_HOLDER, exam_date, 1)
            )
        elif exam_date == second_target_date:
            message_text: str = (
                get_locale(locale, TEXT_IDS.REMINDER_SECOND_MESSAGE)
                .replace(PLACE_HOLDER, subject, 1)
                .replace(PLACE_HOLDER, prof, 1)
                .replace(PLACE_HOLDER, exam_date, 1)
            )
        else:
            continue  # safety check

        try:
            context.bot.send_message(
                chat_id=student_id, text=message_text, parse_mode='Markdown'
            )
            if exam_date == second_target_date:
                DbManager.delete_from(
                    table_name="exams_reg",
                    where="studenti = ? AND insegnamento = ? AND docenti = ?",
                    where_args=(
                        str(student_id),
                        subject,
                        prof,
                    ),
                )
        except Exception as msg_err:  # pylint: disable=broad-exception-caught
            logger.error(
                "Errore nell'invio del messaggio a %s: %s", student_id, msg_err
            )


# gestire quando l'utente seleziona lo stesso appello due volte!!!!!!!!
def reminder_new_handler(update: Update, context: CallbackContext):
    '''Handler to create a new reminder'''
    query = update.callback_query
    query.answer()

    locale = update.callback_query.from_user.language_code
    message_text = get_locale(locale, TEXT_IDS.EXAMS_USAGE_TEXT_ID)
    context.user_data['reminder']['cmd'] = "input_insegnamento"
    context.bot.send_message(
        chat_id=query.message.chat_id,
        text=message_text,
    )


def reminder_del_button(update: Update, context: CallbackContext):
    '''Creating keyaboard to lisk all reminders for a user'''

    query = update.callback_query
    locale = update.callback_query.from_user.language_code
    message_text: str = get_locale(locale, TEXT_IDS.REMINDER_DELETE_SELECTION)

    reminder_list = ExamRegistration.find_by_student(query.message.chat_id)

    context.user_data['reminder']['reminder_list'] = reminder_list

    keyboard: List[List[InlineKeyboardButton]] = [[]]
    keyboard = []
    for idx, item in enumerate(reminder_list):
        button_text = f"{item.insegnamento} - {item.data}"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=f"rem_delete_{idx}")]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.REMINDER_DELETE_ALL),
                callback_data="rem_delete_-1",
            )
        ]
    )

    context.bot.send_message(
        chat_id=query.message.chat_id,
        text=message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def reminder_del_handler(update: Update, context: CallbackContext):
    '''Handler to delete a reminder'''

    query = update.callback_query
    locale = update.callback_query.from_user.language_code

    idx = int(query.data.replace("rem_delete_", ""))

    message_text = ""

    if idx != -1:
        selected_exam = context.user_data['reminder']['reminder_list'][idx]

        try:
            DbManager.delete_from(
                table_name="exams_reg",
                where="studenti = ? AND insegnamento = ? AND docenti = ?",
                where_args=(
                    str(selected_exam.studenti),
                    selected_exam.insegnamento,
                    selected_exam.docenti,
                ),
            )

            message_text: str = (
                get_locale(locale, TEXT_IDS.REMINDER_CONFIRM_DELETE)
                .replace(PLACE_HOLDER, selected_exam.insegnamento, 1)
                .replace(PLACE_HOLDER, selected_exam.data, 1)
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Errore eliminazione record: %s", e)
            message_text: str = get_locale(locale, TEXT_IDS.REPORT_WARNING_TEXT_ID)
    elif idx == -1:
        try:
            DbManager.delete_from(
                table_name="exams_reg",
                where="studenti = ?",
                where_args=(str(query.message.chat_id),),
            )

            message_text: str = get_locale(locale, TEXT_IDS.REMINDER_CONFIRM_DELETE_ALL)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Errore eliminazione record: %s", e)
            message_text: str = get_locale(locale, TEXT_IDS.REPORT_WARNING_TEXT_ID)

    context.bot.send_message(
        chat_id=query.message.chat_id,
        text=message_text,
        parse_mode='Markdown',
    )


def reminder_input_insegnamento(update: Update, context: CallbackContext) -> None:
    """Catches the 'ins: <subject>', queries the DB, and asks for the professor."""
    if not context.user_data or 'reminder' not in context.user_data:
        return

    locale = update.message.from_user.language_code

    raw_subject = re.sub(r"^(?!=<[/])[Ii]ns:\s+", "", update.message.text)
    if context.user_data['reminder'].get('cmd', None) == "input_insegnamento":
        exams = Exam.find("", "", "", raw_subject)

        if not exams:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text=get_locale(
                    locale, TEXT_IDS.REMINDER_NOT_FOUND_SUBJECT_TEXT_ID
                ).replace(PLACE_HOLDER, raw_subject),
            )
            return

        unique_exams = []
        seen = set()
        for exam in exams:
            subj = getattr(exam, 'insegnamento', 'Sconosciuto')
            prof = getattr(exam, 'docenti', 'Sconosciuto')
            if (subj, prof) not in seen:
                unique_exams.append({'subj': subj, 'prof': prof})
                seen.add((subj, prof))

        if not unique_exams:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text=get_locale(locale, TEXT_IDS.REMINDER_NOT_FOUND_PROFESSOR_TEXT_ID),
            )
            return

        if 'temp_exams_list' in context.user_data['reminder']:
            context.user_data['reminder']['temp_exams_list'].clear()
        else:  # crea il dict che conterrà i dati del comando /reminder all'interno della key ['reminder'] di user data
            context.user_data['reminder']['temp_exams_list'] = {}

        context.user_data['reminder']['temp_exams_list'] = unique_exams

        del context.user_data['reminder']['cmd']

        keyboard = []
        for idx, item in enumerate(unique_exams):
            button_text = f"{item['subj']} - {item['prof']}"
            keyboard.append(
                [InlineKeyboardButton(button_text, callback_data=f"rem_prof_{idx}")]
            )

        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=get_locale(locale, TEXT_IDS.REMINDER_SELECT_EXAM_PROFESSOR),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


def reminder_prof_handler(update: Update, context: CallbackContext) -> None:
    """Handles the inline button click for the professor selection."""
    query = update.callback_query
    query.answer()

    if not context.user_data or 'reminder' not in context.user_data:
        return

    idx = int(query.data.replace("rem_prof_", ""))

    selected_exam = context.user_data['reminder']['temp_exams_list'][idx]

    context.user_data['reminder']['insegnamento'] = selected_exam['subj']
    context.user_data['reminder']['professore'] = selected_exam['prof']

    del context.user_data['reminder']['temp_exams_list']

    reminder_button_sessione(
        update=update,
        context=context,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )


def reminder_sessione_handler(update: Update, context: CallbackContext) -> None:
    """Handles the inline button click for the session selection."""
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    if not context.user_data or 'reminder' not in context.user_data:
        return

    sessione_id = query.data.replace("rem_sess_", "")
    context.user_data['reminder']['sessione'] = sessione_id

    reminder_button_appello(
        update=update, context=context, chat_id=chat_id, message_id=message_id
    )


def reminder_button_sessione(
    update: Update, context: CallbackContext, chat_id: int, message_id: int
) -> None:
    """Called by one of the buttons of the /reminder command.
    Allows the user to choose a session among the ones proposed

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    locale = update.callback_query.from_user.language_code
    message_text: str = get_locale(locale, TEXT_IDS.EXAMS_SELECT_SESSION_TEXT_ID)

    keyboard: List[List[InlineKeyboardButton]] = [[]]
    keyboard = [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.EXAMS_SESSION_1_TEXT_ID),
                callback_data="rem_sess_prima",
            ),
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.EXAMS_SESSION_2_TEXT_ID),
                callback_data="rem_sess_seconda",
            ),
        ],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.EXAMS_SESSION_3_TEXT_ID),
                callback_data="rem_sess_terza",
            ),
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.EXAMS_SESSION_4_TEXT_ID),
                callback_data="rem_sess_straordinaria",
            ),
        ],
    ]

    context.bot.editMessageText(
        text=message_text,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def reminder_appello_handler(update: Update, context: CallbackContext) -> None:
    """Handles the inline button click for the exam date selection."""
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    locale = update.callback_query.from_user.language_code

    if not context.user_data or 'reminder' not in context.user_data:
        return

    date_id = query.data.replace("rem_appello_", "")
    context.user_data['reminder']['appello'] = date_id

    data = context.user_data['reminder']
    esame = data.get('insegnamento', 'N/D')
    prof = data.get('professore', 'N/D')
    data_scelta = data.get('appello', 'Data selezionata')

    message_text: str = (
        get_locale(locale, TEXT_IDS.REMINDER_RECAP)
        .replace(PLACE_HOLDER, esame, 1)
        .replace(PLACE_HOLDER, prof, 1)
        .replace(PLACE_HOLDER, data_scelta, 1)
    )

    keyboard: List[List[InlineKeyboardButton]] = [[]]
    keyboard = [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CONFIRM), callback_data="rem_conf_yes"
            ),
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.UNDO), callback_data="rem_conf_no"
            ),
        ]
    ]

    context.bot.editMessageText(
        text=message_text,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
    )


def reminder_confermato_handler(update: Update, context: CallbackContext):
    '''Handler per gestire conferma richiesta'''
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    locale = update.callback_query.from_user.language_code

    u_data = context.user_data.get('reminder', {})
    raw_date = u_data.get('appello', 'Data selezionata')
    clean_date_str = str(raw_date).split(' ', maxsplit=1)[0]

    try:
        data_obj = datetime.strptime(clean_date_str, '%d/%m/%Y').date()
    except (ValueError, TypeError):
        try:
            data_obj = datetime.strptime(clean_date_str, '%d-%m-%Y').date()
        except (ValueError, TypeError):
            data_obj = raw_date

    insegnamento = u_data.get('insegnamento', 'N/D')
    docenti = u_data.get('professore', 'N/D')

    nuovo_reminder = ExamRegistration(
        studenti=str(chat_id),
        insegnamento=insegnamento,
        docenti=docenti,
        data=data_obj,
        lingua=locale,
    )

    results = DbManager.select_from(
        table_name="exams_reg",
        where="studenti = ? AND docenti = ? AND insegnamento = ?",
        where_args=(str(chat_id), str(docenti), str(insegnamento)),
    )

    if not results:

        if (data_obj - date.today()).days > 4:
            try:
                nuovo_reminder.save()
                message_text: str = get_locale(
                    locale, TEXT_IDS.REMINDER_CONFIRM_REGISTRATION
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Errore salvataggio DB: %s", e)
                message_text: str = get_locale(
                    locale, TEXT_IDS.REMINDER_DUPLICATE_WARNING
                )
        else:
            message_text: str = get_locale(locale, TEXT_IDS.REMINDER_TOO_LATE)

    else:
        message_text: str = get_locale(locale, TEXT_IDS.REMINDER_DUPLICATE_WARNING)

    u_data.clear()

    context.bot.editMessageText(
        text=message_text,
        chat_id=chat_id,
        message_id=message_id,
        parse_mode='Markdown',
    )


def reminder_annullato_handler(update: Update, context: CallbackContext):
    '''Handler per gestire annullamento richiesta'''
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    locale = update.callback_query.from_user.language_code

    del context.user_data['reminder']

    message_text: str = get_locale(locale, TEXT_IDS.UNDO_OPERATION)

    context.bot.editMessageText(
        text=message_text, chat_id=chat_id, message_id=message_id
    )


def reminder_button_appello(
    update: Update, context: CallbackContext, chat_id: int, message_id: int
) -> None:
    """Called by one of the buttons of the /reminder command.
    Allows the user to choose an exam date among the ones proposed
    """
    locale = update.callback_query.from_user.language_code

    subject = context.user_data['reminder'].get('insegnamento', '')
    prof = context.user_data['reminder'].get('professore', '')
    session = context.user_data['reminder'].get('sessione', '')

    all_exams = Exam.find("", "", "", subject)

    valid_dates = []
    for exam in all_exams:
        exam_prof = getattr(exam, 'docenti', '')
        exam_date_string = getattr(exam, session, '')

        if exam_prof != prof or not exam_date_string:
            continue

        try:
            actual_dates = ast.literal_eval(exam_date_string)
        except (ValueError, SyntaxError):
            actual_dates = exam_date_string

        if not isinstance(actual_dates, list):
            actual_dates = [actual_dates]

        for single_date in actual_dates:
            date_str = str(single_date)
            if date_str not in valid_dates:
                valid_dates.append(date_str)

    keyboard = []
    if len(valid_dates) > 0:
        for _, exam_date in enumerate(valid_dates):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        exam_date, callback_data=f"rem_appello_{exam_date}"
                    )
                ]
            )
        message_text: str = get_locale(
            locale, TEXT_IDS.REMINDER_SELECT_EXAM_DATE_TEXT_ID
        )
    else:
        message_text: str = get_locale(locale, TEXT_IDS.REMINDER_NO_EXAM_DATE)

    context.bot.editMessageText(
        text=message_text,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
    )
