"""Job updater"""

import logging
from datetime import datetime, timedelta

from telegram.ext import CallbackContext

from module.commands.reminder import reminder_send_message
from module.data import Exam, Lesson, Professor, TimetableSlot
from module.data.db_manager import DbManager
from module.shared import check_print_old_exams, get_year_code

logger = logging.getLogger(__name__)


def check_exam_reminders(context: CallbackContext) -> None:
    """Job function to check for exams 14 days and 4 days from now and send reminder."""

    now = datetime.now()

    first_target_date = (now + timedelta(days=14)).strftime('%Y-%m-%d')
    second_target_date = (now + timedelta(days=4)).strftime('%Y-%m-%d')

    try:
        # select al db che prende solo gli esami tra 4 o 14 giorni
        reminders = DbManager.select_from(
            table_name="exams_reg",
            where="data IN (?, ?)",
            where_args=(first_target_date, second_target_date),
        )

        if reminders:
            reminder_send_message(
                reminders, context, first_target_date, second_target_date
            )

    except Exception as db_err:  # pylint: disable=broad-exception-caught
        logger.error(
            "Database error nel controllo all'interno della funzione check_exam_reminders: %s",
            db_err,
        )


def updater_lep(_: CallbackContext):
    """Called with a set frequence.
    Updates all the scrapables

    Args:
        context: context passed by the handler
    """
    year_exam = get_year_code(
        11, 30
    )  # aaaa/12/01 (cambio nuovo anno esami) data dal quale esami del vecchio a nuovo anno coesistono

    Exam.scrape(
        f"1{year_exam}", delete=True
    )  # flag che permette di eliminare tutti gli esami presenti in tabella exams
    if check_print_old_exams(year_exam):
        Exam.scrape(f"1{int(year_exam) - 1}")

    Professor.scrape(delete=True)
    TimetableSlot.scrape(delete=True)
    Lesson.scrape(
        f"1{get_year_code(9, 20)}", delete=True
    )  # aaaa/09/21 (cambio nuovo anno lezioni) data dal quale vengono prelevate le lezioni del nuovo anno
