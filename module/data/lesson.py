# -*- coding: utf-8 -*-
"""Lesson class"""
import logging
from typing import List
import bs4
import requests
from module.data.db_manager import DbManager
from module.data.scrapable import Scrapable

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class Lesson(Scrapable):
    """Lesson

    Attributes:
        nome (:class:`str`): name of the subject
        giorno_settimana (:class:`str`): day of the week
        ora_inizio (:class:`str`): starting time of the lesson
        ora_fine (:class:`str`): ending time of the lesson
        aula (:class:`str`): hall
        anno (:class:`str`): year
        semestre (:class:`str`): semester
    """
    IDS = ["l-31", "l-35", "lm-18", "lm-40"]
    DAY_TO_INT = {'LUN': 1, 'MAR': 2, 'MER': 3, 'GIO': 4, 'VEN': 5}
    INT_TO_DAY = {'1': "LUN", '2': "MAR", '3': "MER", '4': "GIO", '5': "VEN"}

    # pylint: disable=too-many-arguments
    def __init__(self,
                 nome: str = "",
                 giorno_settimana: str = "",
                 ora_inizio: str = "",
                 ora_fine: str = "",
                 aula: str = "",
                 anno: str = "",
                 semestre: str = ""):
        self.nome = nome
        self.giorno_settimana = giorno_settimana
        self.ora_inizio = ora_inizio
        self.ora_fine = ora_fine
        self.aula = aula
        self.anno = anno
        self.semestre = semestre

    @property
    def table(self) -> str:
        """name of the database table that will store this Lesson"""
        return "lessons"

    @property
    def columns(self) -> tuple:
        """tuple of column names of the database table that will store this Lesson"""
        return ("nome", "giorno_settimana", "ora_inizio", "ora_fine", "aula", "anno", "semestre")

    @classmethod
    def scrape(cls, year_exams: str, delete: bool = False):
        """Scrapes the lessons of the provided year and stores them in the database

        Args:
            year_exams: current year
            delete: whether the table contents should be deleted first. Defaults to False.
        """
        lessons = []
        # pylint: disable=too-many-nested-blocks
        for id_ in cls.IDS:
            urls = [
                "http://web.dmi.unict.it/corsi/" + str(id_) + "/orario-lezioni?semestre=1&aa=" + year_exams,
                "http://web.dmi.unict.it/corsi/" + str(id_) + "/orario-lezioni?semestre=2&aa=" + year_exams
            ]
            for url in urls:
                sorgente = requests.get(url, timeout=10).text
                soup = bs4.BeautifulSoup(sorgente, "html.parser")

                if soup.find('b', id='attivo').text[0] == 'S':
                    semestre = 2
                elif soup.find('b', id='attivo').text[0] == 'P':
                    semestre = 1

                table = soup.find('table', id='tbl_small_font')

                if not table:
                    # pylint: disable=logging-not-lazy,logging-fstring-interpolation
                    logger.warning(f"Lessons table for `{url}` not found.")
                    break

                tr_all = table.find_all('tr')

                anno = 1
                for tr in tr_all:
                    td_all = tr.find_all('td')
                    # Calcola anno materia
                    td_anno = tr.find('td')
                    if td_anno is not None and (td_anno.text[0] == '2' or td_anno.text[0] == '3'):
                        anno = td_anno.text[0]

                    if len(td_all) == 4:
                        orari = td_all[3]
                        for orario in orari:
                            if str(orario) != '<br/>':
                                giorno = cls.DAY_TO_INT.get(orario[0:3], 0)
                                orario = orario.replace(orario[0:3], '')  #GIORNO
                                ora_inizio = orario[1:6]  #ORA INIZIO
                                ora_fine = orario[7:12]  #ORA FINE
                                orario = orario.replace(ora_inizio + "-" + ora_fine, '')
                                aula = orario[2:]

                                lesson = cls(nome=td_all[0].text,
                                             giorno_settimana=str(giorno),
                                             ora_inizio=ora_inizio,
                                             ora_fine=ora_fine,
                                             aula=str(aula),
                                             anno=str(anno),
                                             semestre=str(semestre))
                                lessons.append(lesson)

        if delete:
            cls.delete_all()
        cls.bulk_save(lessons)
        logger.info("Lessons loaded.")

    @classmethod
    def find(cls, where_anno: str = "", where_giorno: str = "", where_nome: str = "") -> List['Lesson']:
        """Produces a list of lessons from the database, based on the provided parametes

        Args:
            where_anno: specifies the year. Defaults to "".
            where_giorno: specifies the day. Defaults to "".
            where_nome: specifies the name of the subject. Defaults to "".

        Returns:
            result of the query on the database
        """
        if where_giorno:
            where_giorno = f"and (giorno_settimana = {where_giorno})"
        else:
            where_giorno = ""

        if where_anno:
            where_anno = f"and (anno = {where_anno})"
        else:
            where_anno = ""

        db_results = DbManager.select_from(table_name=cls().table, where=f"nome LIKE ? {where_giorno} {where_anno}", where_args=(f'%{where_nome}%',))
        return cls._query_result_initializer(db_results)

    @classmethod
    def find_all(cls) -> List['Lesson']:
        """Finds all the lessons present in the database

        Returns:
            list of all the lessons
        """
        return super().find_all()

    def __repr__(self):
        return f"Lesson: {self.__dict__}"

    def __str__(self):
        return f"*Insegnamento:* {self.nome}"\
                f"\n*Giorno:* {self.__class__.INT_TO_DAY[self.giorno_settimana]}"\
                f"\n*Ora:* {self.ora_inizio} - {self.ora_fine}"\
                f"\n*Anno:* {self.anno}"\
                f"\n*Aula:* {self.aula}\n"
