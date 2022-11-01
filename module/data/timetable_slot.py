# -*- coding: utf-8 -*-
"""TimetableSlot class"""
import logging
from datetime import datetime
from typing import List
import requests
import pandas as pd
from module.data.db_manager import DbManager
from module.data.scrapable import Scrapable

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
class TimetableSlot(Scrapable):
    """TimetableSlot

    Attributes:
        ID (:class:`int`): id of the TimetableSlot
        nome (:class:`str`): name of the subject
        giorno (:class:`str`): days from today
        ora_inizio (:class:`str`): starting time of the lesson
        ora_fine (:class:`str`): ending time of the lesson
        aula (:class:`str`): hall
    """

    # pylint: disable=too-many-arguments
    def __init__(self, ID: int = 0, nome: str = "", giorno: int = 0, ora_inizio: str = "", ora_fine: str = "", aula: str = ""):
        self.ID = ID
        self.nome = nome
        self.giorno = giorno
        self.ora_inizio = ora_inizio
        self.ora_fine = ora_fine
        self.aula = aula

    @property
    def table(self) -> str:
        """name of the database table that will store this TimetableSlot"""
        return "timetable_slots"

    @property
    def columns(self) -> tuple:
        """tuple of column names of the database table that will store this TimetableSlot"""
        return ("ID", "nome", "giorno", "ora_inizio", "ora_fine", "aula")

    @property
    def end_hour(self) -> str:
        """adds half an hour to the ora_fine value"""
        if self.ora_fine[3:] == '30':
            return "{00}:00".format(int(self.ora_fine[:2]) + 1) # pylint: disable=consider-using-f-string
        return self.ora_fine[:3] + '30'

    @property
    def is_still_to_come(self) -> bool:
        """whether or not the current time slot is still to come or has already passed"""
        end_time = self.end_hour.split(":")
        now = datetime.now()
        last = now.replace(hour=int(end_time[0]), minute=int(end_time[1]), second=0, microsecond=0)
        return now < last

    @classmethod
    def scrape(cls, delete: bool = False):
        """Scrapes the timetable slots of the provided year and stores them in the database

        Args:
            delete: whether the table contents should be deleted first. Defaults to False.
        """
        timetable_slots = []

        # avoid circular import without using read_md
        with open("data/markdown/aulario.md", "r", encoding="utf8") as in_file:
            aulario_url = in_file.read()


        response = requests.get(aulario_url, timeout=10).text
        tables = pd.read_html(response)

        for k, table in enumerate(tables):
            rooms = table.iloc[:, 0]
            schedule = table.iloc[:, 1:]
            subjects = {}
            for time in schedule:
                for i, row in enumerate(table[time]):
                    if time[-1] == "1":
                        time = time[:3] + "30"
                    if not pd.isnull(row):
                        r = row[:20] + rooms[i]
                        if not r in subjects:
                            subjects[r] = cls(nome=row.replace('[]', '').replace('[', '(').replace(']', ')'),
                                              giorno=k,
                                              ora_inizio=time,
                                              ora_fine=time,
                                              aula=rooms[i])
                        else:
                            subjects[r].ora_fine = time
            timetable_slots.extend(subjects.values())

        if delete:
            cls.delete_all()

        offset = DbManager.count_from(table_name=cls().table)  # number of rows already present
        for i, timetable_slot in enumerate(timetable_slots):
            timetable_slot.ID = i + offset  # generate the ID of the timetable slot based on its position in the array
        cls.bulk_save(timetable_slots)
        logger.info("Aulario loaded.")

    @classmethod
    def find(cls, **kwargs) -> List['TimetableSlot']:
        """Produces a list of scrapables from the database, based on the provided parametes

        Returns:
            result of the query on the database
        """
        return super()._find(**kwargs)

    @classmethod
    def find_all(cls) -> List['TimetableSlot']:
        """Finds all the timetable slots present in the database

        Returns:
            list of all the timetable slots
        """
        return super().find_all()

    @classmethod
    def get_max_giorno(cls) -> int:
        """Finds the maximum value of giorno

        Returns:
            result of the query on the database
        """
        db_results = DbManager.select_from(select="MAX(giorno) as g", table_name=cls().table)
        if not db_results or db_results[0]['g'] is None:
            return 0
        return int(db_results[0]['g'])

    def __repr__(self):
        return f"TimetableSlot: {self.__dict__}"
