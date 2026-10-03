# -*- coding: utf-8 -*-
"""TimetableSlot class"""

import logging
from datetime import date, datetime
from io import StringIO
from typing import List, Optional

import pandas as pd
import requests

from module.data.db_manager import DbManager
from module.data.scrapable import Scrapable

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


class TimetableSlot(Scrapable):
    """TimetableSlot

    Attributes:
        ID (:class:`int`): id of the TimetableSlot
        nome (:class:`str`): name of the subject
        giorno (:class:`str`): date of the lesson, in ISO format (YYYY-MM-DD)
        ora_inizio (:class:`str`): starting time of the lesson
        ora_fine (:class:`str`): ending time of the lesson
        aula (:class:`str`): hall
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        ID: int = 0,
        nome: str = "",
        giorno: str = "",
        ora_inizio: str = "",
        ora_fine: str = "",
        aula: str = "",
    ):
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
            return f"{int(self.ora_fine[:2]) + 1}:00"
        return self.ora_fine[:3] + '30'

    @property
    def is_still_to_come(self) -> bool:
        """whether or not the current time slot is still to come or has already passed"""
        end_time = self.end_hour.split(":")
        now = datetime.now()
        last = now.replace(
            hour=int(end_time[0]), minute=int(end_time[1]), second=0, microsecond=0
        )
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
        tables = pd.read_html(StringIO(response))

        for table in tables:
            # the first header cell holds the day, e.g. "Venerdì, 09/10/2026"
            day = (
                datetime.strptime(
                    str(table.columns[0]).rsplit(", ", maxsplit=1)[-1], "%d/%m/%Y"
                )
                .date()
                .isoformat()
            )
            rooms = table.iloc[:, 0]
            schedule = table.iloc[:, 1:]
            subjects = {}
            for time in schedule:
                for i, row in enumerate(table[time]):
                    if time[-1] == "1":
                        time = time[:3] + "30"
                    if not pd.isnull(row):
                        r = row[:20] + rooms[i]
                        if r not in subjects:
                            subjects[r] = cls(
                                nome=row.replace('[]', '')
                                .replace('[', '(')
                                .replace(']', ')'),
                                giorno=day,
                                ora_inizio=time,
                                ora_fine=time,
                                aula=rooms[i],
                            )
                        else:
                            subjects[r].ora_fine = time
            timetable_slots.extend(subjects.values())

        if delete:
            cls.delete_all()

        offset = DbManager.count_from(
            table_name=cls().table
        )  # number of rows already present
        for i, timetable_slot in enumerate(timetable_slots):
            timetable_slot.ID = (
                i + offset
            )  # generate the ID of the timetable slot based on its position in the array
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
    def get_last_day(cls) -> Optional[date]:
        """Finds the last day with at least one timetable slot

        Returns:
            the last day, or None if there are no timetable slots
        """
        # rows scraped by older versions store giorno as an integer day offset,
        # and stay in the table until the next successful scrape replaces them
        db_results = DbManager.select_from(
            select="MAX(giorno) as g",
            table_name=cls().table,
            where="typeof(giorno) = 'text'",
        )
        if not db_results or db_results[0]['g'] is None:
            return None
        return date.fromisoformat(db_results[0]['g'])

    def __repr__(self):
        return f"TimetableSlot: {self.__dict__}"
