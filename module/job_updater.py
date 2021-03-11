import re
import sqlite3
from telegram.ext import CallbackContext
from module.shared import check_print_old_exams, get_year_code
from module.scraper_professors import scrape_prof
from module.scraper_lessons import scrape_lessons
from module.scraper_exams import scrape_exams


def initialize_database():
    """Makes sure the database is initialized correctly.
    Executes all the queries located in the data/DMI_DB.sql file
    """
    with open("data/DMI_DB.sql", "r") as f:
        queries = re.split(pattern=r"(?<=\);)\s", string=f.read())
        conn = sqlite3.connect('data/DMI_DB.db')
        for query in queries:
            conn.execute(query)
        conn.commit()
        conn.close()


def updater_lep(context: CallbackContext) -> None:
    initialize_database()

    year_exam = get_year_code(11 , 30)               # aaaa/12/01 (cambio nuovo anno esami) data dal quale esami del vecchio a nuovo anno coesistono

    scrape_exams("1" + str(year_exam), delete= True) # flag che permette di eliminare tutti gli esami presenti in tabella exams
    if (check_print_old_exams(year_exam)):
        scrape_exams("1" + str(int(year_exam) - 1))

    scrape_lessons("1" + str(get_year_code(9 , 20))) # aaaa/09/21 (cambio nuovo anno lezioni) data dal quale vengono prelevate le lezioni del nuovo anno
    scrape_prof()
