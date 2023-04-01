# -*- coding: utf-8 -*-
"""Exam class"""
from typing import List, Optional
import logging
import re
import bs4
import requests
from module.data.scrapable import Scrapable
from module.data.db_manager import DbManager

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class Exam(Scrapable):
    """Exam

    Attributes:
        anno (:class:`str`): [1° anno | 2° anno | 3° anno]
        cdl (:class:`str`): "Corso Di Laurea"
        insegnamento (:class:`str`): subject of the exam
        docenti (:class:`str`): name of the teacher
        prima (:class:`list | str`): list of appeals in the first session
        seconda (:class:`list | str`): list of appeals in the second session
        terza (:class:`list | str`): list of appeals in the second session
        straordinaria (:class:`list | str`): list of appeals in the "straordinaria" session
    """
    COURSES = ["l-31", "lm-18", "l-35", "lm-40"]
    SESSIONS = ["prima", "seconda", "terza", "straordinaria"]

    def __init__(self, anno: str = "", cdl: str = "", insegnamento: str = "", docenti: str = ""):
        self.anno = anno
        self.cdl = cdl
        self.insegnamento = insegnamento
        self.docenti = docenti
        self.prima = []
        self.seconda = []
        self.terza = []
        self.straordinaria = []

    @property
    def table(self) -> str:
        """name of the database table that will store this Exam"""
        return "exams"

    @property
    def columns(self) -> tuple:
        """tuple of column names of the database table that will store this Exam"""
        return ("anno", "cdl", "insegnamento", "docenti", "prima", "seconda", "terza", "straordinaria")

    @property
    def values(self) -> tuple:
        """tuple of values that will be saved in the database"""
        return (
            self.anno, self.cdl, self.insegnamento, self.docenti, str(self.prima), str(self.seconda), str(self.terza),
            str(self.straordinaria))

    # pylint: disable=inconsistent-return-statements
    def get_session(self, session_name: str) -> Optional[list]:
        """Gets the session with the same name.

        Args:
            session_name: [ prima | seconda | terza | straordinaria ]

        Returns:
            session
        """
        if session_name in self.__class__.SESSIONS:
            # pylint: disable=unnecessary-dunder-call
            return self.__getattribute__(session_name)

    def append_session(self, session_name: str, to_append: str):
        """Appends an element to a session based on its name.

        Args:
            session_name: [ prima | seconda | terza | straordinaria ]
            to_append: element to append
        """
        if session_name in self.__class__.SESSIONS:
            # pylint: disable=unnecessary-dunder-call
            self.__getattribute__(session_name).append(to_append)

    @classmethod
    def append_multiple_sessions(cls, cells, exam, session):
        for cell in cells:
            cell_clean_text = cell.text.replace('\xa0', '').replace('\n', '').replace('DMI', '')
            exam_sessions = exam.get_session("prima") + exam.get_session("seconda") + exam.get_session(
                "terza") + exam.get_session("straordinaria")
            current_exams = [string.replace('DMI', '') for string in exam_sessions]
            if cell_clean_text not in current_exams and cell_clean_text != "":
                exam.append_session(session, cell_clean_text)

    def delete(self):
        """Deletes this exam from the database"""
        where = "anno = ? and cdl = ? and insegnamento = ? and docenti = ?"
        values = (self.anno, self.cdl, self.insegnamento, self.docenti)
        DbManager.delete_from(table_name=self.table, where=where, where_args=values)

    @classmethod
    def scrape(cls, year_exams: str, delete: bool = False):
        """Scrapes the exams of the provided year and stores them in the database

        Args:
            year_exams: current year
            delete: whether the table contents should be deleted first. Defaults to False.
        """
        url_exams = {
            "l-31": [  # Informatica Triennale
                f"http://web.dmi.unict.it/corsi/l-31/esami?sessione=1&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/l-31/esami?sessione=2&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/l-31/esami?sessione=3&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/l-31/esami?sessione=4&aa=1{year_exams}"
            ],
            "lm-18": [  # Informatica Magistrale
                f"http://web.dmi.unict.it/corsi/lm-18/esami?sessione=1&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/lm-18/esami?sessione=2&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/lm-18/esami?sessione=3&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/lm-18/esami?sessione=4&aa=1{year_exams}"
            ],
            "l-35": [  # Matematica Triennale
                f"http://web.dmi.unict.it/corsi/l-35/esami?sessione=1&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/l-35/esami?sessione=2&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/l-35/esami?sessione=3&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/l-35/esami?sessione=4&aa=1{year_exams}"
            ],
            "lm-40": [  # Matematica Magistrale
                f"http://web.dmi.unict.it/corsi/lm-40/esami?sessione=1&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/lm-40/esami?sessione=2&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/lm-40/esami?sessione=3&aa=1{year_exams}",
                f"http://web.dmi.unict.it/corsi/lm-40/esami?sessione=4&aa=1{year_exams}"
            ]
        }

        course_dict = {
            "l-31": "Informatica Triennale",
            "lm-18": "Informatica Magistrale",
            "l-35": "Matematica Triennale",
            "lm-40": "Matematica Magistrale"
        }

        exams = []
        year = ""

        # pylint: disable=too-many-nested-blocks
        for course in cls.COURSES:
            for count, url in enumerate(url_exams[course]):
                source = requests.get(url, timeout=10).text
                soup = bs4.BeautifulSoup(source, "html.parser")
                table = soup.find(id="table-exams")
                rows = table.find_all("tr")[1:]  # e dalla tabella estraiamo l'array con tutte le righe

                for row in rows:  # scorriamo riga per riga
                    # se la riga ha solo td, allora contiene solo l'anno della materia (non ci interessa)
                    if not len(row.find_all("td")) == 1:
                        # adesso che sappiamo che è una materia, estraiamo tutte le celle per ottenere i dati su di essa
                        cells = row.find_all("td")
                        # in base al valore di count sappiamo la sessione che stiamo analizzando
                        session = cls.SESSIONS[count]
                        # variabile sentinella per vedere se la materia che stiamo analizzando
                        # è già presente dentro l'array
                        flag = False

                        # scorriamo tutte le materie fino ad ora inserite (inizialmente, banalmente, saranno 0)
                        for exam in exams:
                            if (cells[1]).text == exam.insegnamento and (cells[2]).text == exam.docenti:
                                # se abbiamo trovato la materia nell'array
                                # dobbiamo solo aggiungere gli appelli della nuova sessione > 1
                                flag = True
                                # dato che la materia è già presente nell'array, i primi 3 valori (id, docenti e
                                # nome) non ci interessano
                                cls.append_multiple_sessions(cells[3:], exam, session)

                        # se non abbiamo trovato la materia che stiamo analizzando attualmente nell'array delle materie
                        # vuol dire che nelle sessioni precedenti non aveva appelli (oppure è la prima sessione)
                        if not flag:
                            course_name = course_dict[course]

                            # creiamo una nuova istanza di esame da riempire con i dati trovati
                            new_exam = cls(anno=year, cdl=course_name, insegnamento=cells[1].text,
                                           docenti=cells[2].text)

                            cls.append_multiple_sessions(cells[3:], new_exam, session)
                            exams.append(new_exam)  # aggiungiamo l'esame trovato alla lista

                    else:  # se la row ha solo un td figlio, è la riga che indica l'anno delle materie successive
                        # quindi aggiorniamo la variabile anno con il valore della prima cella della riga
                        year = row.find("td").text

        if delete:
            cls.delete_all()
        cls.bulk_save(exams)  # infine, salviamo tutti gli esami nel database
        logger.info("Exams loaded.")

    @classmethod
    def find(cls, select_sessione: str = "", where_sessione: str = "", where_anno: str = "",
             where_insegnamento: str = "") -> List['Exam']:
        """Produces a list of exams from the database, based on the provided parametes

        Args:
            select_sessione: which sessions to select. Defaults to "".
            where_sessione: specifies what sessions can't be []. Defaults to "".
            where_anno: specifies the year. Defaults to "".
            where_insegnamento: specifies the subject. Defaults to "".

        Returns:
            result of the query on the database
        """
        if not select_sessione:
            select_sessione = "prima, seconda, terza, straordinaria"

        if where_sessione:
            where_sessione = f"and (not {where_sessione} = '[]')"
        else:
            where_sessione = ""

        if where_anno:
            where_anno = f"and (anno = '{where_anno}')"
        else:
            where_anno = ""

        db_results = DbManager.select_from(select=f"anno, cdl, docenti, insegnamento, {select_sessione}",
                                           table_name=cls().table,
                                           where=f"insegnamento LIKE ? {where_sessione} {where_anno}",
                                           where_args=(f'%{where_insegnamento}%',))
        return cls._query_result_initializer(db_results)

    @classmethod
    def find_all(cls) -> List['Exam']:
        """Finds all the exams present in the database

        Returns:
            list of all the exams
        """
        return super().find_all()

    def __repr__(self):
        return f"Exam: {self.__dict__}"

    def __str__(self):
        output = "*Insegnamento:* " + self.insegnamento
        output += "\n*Docenti:* " + self.docenti

        for session in self.__class__.SESSIONS:
            if self.get_session(session):
                appeals = str(self.get_session(session))
                #aggiunge un - per separare orario e luogo dell'esame
                appeals = re.sub(r"(?P<ora>([01]?\d|2[0-3]):[0-5][0-9])(?P<parola>\w)", r"\g<ora> - \g<parola>",
                                 appeals)
                # separa i vari appelli della sessione
                appeals = re.split(r"[\"'], [\"']", appeals)

                for i, appeal in enumerate(appeals):
                    # rimuove eventuali caratteri [ ' ] rimasti in ogni appello
                    appeals[i] = re.sub(r"[\['\]]", "", appeal)
                    # cattura eventuali link e li rende inoffensivi per il markdown
                    appeals[i] = re.sub(
                        r"(?P<link>https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))",
                        r"[link](\g<link>)", appeals[i])
                    # rimuove eventuali caratteri * e _ rimasti che non siano nei link
                    appeals[i] = re.sub(r"[*_](?![^(]*[)])", " ", appeals[i])

                if "".join(appeals) != "":
                    output += "\n\n*" + session.title() + ":*\n" + "\n".join(appeals)

        output += "\n*CDL:* " + self.cdl
        output += "\n*Anno:* " + self.anno + "\n"

        return output
