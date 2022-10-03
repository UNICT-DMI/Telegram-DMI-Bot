"""Job updater"""
from telegram.ext import CallbackContext
from module.shared import check_print_old_exams, get_year_code
from module.data import Exam, Lesson, Professor, TimetableSlot


def updater_lep(context: CallbackContext):
    """Called with a set frequence.
    Updates all the scrapables

    Args:
        context: context passed by the handler
    """
    year_exam = get_year_code(11, 30)  # aaaa/12/01 (cambio nuovo anno esami) data dal quale esami del vecchio a nuovo anno coesistono

    Exam.scrape(f"1{year_exam}", delete=True)  # flag che permette di eliminare tutti gli esami presenti in tabella exams
    if check_print_old_exams(year_exam):
        Exam.scrape(f"1{int(year_exam) - 1}")

    Professor.scrape(delete=True)
    TimetableSlot.scrape(delete=True)
    Lesson.scrape(f"1{get_year_code(9, 20)}", delete=True)  # aaaa/09/21 (cambio nuovo anno lezioni) data dal quale vengono prelevate le lezioni del nuovo anno
