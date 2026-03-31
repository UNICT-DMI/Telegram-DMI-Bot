# -*- coding: utf-8 -*-
"""Reminder class"""

import logging
from typing import List

from module.data.db_manager import DbManager
from module.data.scrapable import Scrapable

logger = logging.getLogger(__name__)


class ExamRegistration(Scrapable):
    """Reminder per gli esami

    Attributes:
        studenti (:class:`str`): student id who wants to receive a reminder
        insegnamento (:class:`str`): subject of the exam
        docenti (:class:`str`): name of the teacher
        data (:class:`date`): date of the exam
        lingua (:class:`str`): language code of the student who wants to receive a reminder
    """

    def __init__(
        self,
        studenti: str = "",
        insegnamento: str = "",
        docenti: str = "",
        data: str = "",
        lingua: str = "",
    ):
        self.studenti = studenti
        self.insegnamento = insegnamento
        self.docenti = docenti
        self.data = data
        self.lingua = lingua

    @property
    def table(self) -> str:
        """name of the database table that will store this Reminder"""
        return "exams_reg"

    @property
    def columns(self) -> tuple:
        """tuple of column names of the database table that will store this Reminder"""
        return ("studenti", "insegnamento", "docenti", "data", "lingua")

    @classmethod
    def find_by_student(cls, studente_id: str) -> List['ExamRegistration']:
        """Produces a list of reminders from the database for a specific student

        Args:
            studente_id: ID of the student

        Returns:
            List of Reminder objects
        """
        db_results = DbManager.select_from(
            table_name=cls().table, where="studenti = ?", where_args=(studente_id,)
        )
        return cls._query_result_initializer(db_results)

    def __repr__(self):
        return f"Reminder: {self.__dict__}"

    def __str__(self):
        return (
            f"Registrazione Promemoria Esame\n"
            f"ID Studente: {self.studenti}\n"
            f"Materia: {self.insegnamento}\n"
            f"Docente: {self.docenti}\n"
            f"Data: {self.data}\n"
            f"Lingua: {self.lingua}\n"
        )
