from module.shared import check_print_old_exams, get_year_code
from module.scraper_professors import scrape_prof
from module.scraper_lessons import scrape_lessons
from module.scraper_exams import scrape_exams

def updater_lep(context):
    year_exam = get_year_code(11 , 30) # aaaa/12/01 (cambio nuovo anno esami) data dal quale esami del vecchio a nuovo anno coesistono
    scrape_exams("1" + str(year_exam), delete= True) # flag che permette di eliminare tutti gli esami presenti in tabella exams
    if(check_print_old_exams(year_exam)):
        scrape_exams("1" + str(int(year_exam) - 1))
    scrape_lessons("1" + str(get_year_code(9 , 20))) # aaaa/09/21 (cambio nuovo anno lezioni) data dal quale vengono prelevate le lezioni del nuovo anno
    scrape_prof()