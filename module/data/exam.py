# -*- coding: utf-8 -*-
"""Exam class"""
from typing import List
import logging
import re
import bs4
import requests
from module.data.scrapable import Scrapable
from module.data.db_manager import DbManager

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


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
    SESSIONS = ["prima", "seconda", "terza", "straordinaria"]  # "straordinaria" non è considerata per lo scraping

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
        return (self.anno, self.cdl, self.insegnamento, self.docenti, str(self.prima), str(self.seconda), str(self.terza), str(self.straordinaria))

    def get_session(self, session_name: str) -> list:
        """Gets the session with the same name.

        Args:
            session_name: [ prima | seconda | terza | straordinaria ]

        Returns:
            session
        """
        if session_name in self.__class__.SESSIONS:
            return self.__getattribute__(session_name)

    def append_session(self, session_name: str, to_append: str):
        """Appends an element to a session based on its name.

        Args:
            session_name: [ prima | seconda | terza | straordinaria ]
            to_append: element to append
        """
        if session_name in self.__class__.SESSIONS:
            self.__getattribute__(session_name).append(to_append)

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
                f"http://web.dmi.unict.it/corsi/l-31/esami?sessione=1&aa={year_exams}",
                f"http://web.dmi.unict.it/corsi/l-31/esami?sessione=2&aa={year_exams}",
                f"http://web.dmi.unict.it/corsi/l-31/esami?sessione=3&aa={year_exams}"
            ],
            "lm-18": [  # Informatica Magistrale
                f"http://web.dmi.unict.it/corsi/lm-18/esami?sessione=1&aa={year_exams}",
                f"http://web.dmi.unict.it/corsi/lm-18/esami?sessione=2&aa={year_exams}",
                f"http://web.dmi.unict.it/corsi/lm-18/esami?sessione=3&aa={year_exams}"
            ],
            "l-35": [  # Matematica Triennale
                f"http://web.dmi.unict.it/corsi/l-35/esami?sessione=1&aa={year_exams}",
                f"http://web.dmi.unict.it/corsi/l-35/esami?sessione=2&aa={year_exams}",
                f"http://web.dmi.unict.it/corsi/l-35/esami?sessione=3&aa={year_exams}"
            ],
            "lm-40": [  # Matematica Magistrale
                f"http://web.dmi.unict.it/corsi/lm-40/esami?sessione=1&aa={year_exams}",
                f"http://web.dmi.unict.it/corsi/lm-40/esami?sessione=2&aa={year_exams}",
                f"http://web.dmi.unict.it/corsi/lm-40/esami?sessione=3&aa={year_exams}"
            ]
        }
        exams = []
        year = ""

        for course in cls.COURSES:
            for count, url in enumerate(url_exams[course]):
                source = requests.get(url).text
                soup = bs4.BeautifulSoup(source, "html.parser")
                table = soup.find(id="tbl_small_font")
                rows = table.find_all("tr")  # e dalla tabella estraiamo l'array con tutte le righe

                for row in rows:  # e scorriamo riga per riga

                    if not row.has_attr("class"):
                        # se non ha l'attributo class potrebbe essere una materia oppure l'anno (altrimenti è la riga delle informazioni che non ci interessa)
                        firstcell = row.find("td")  # estraiamo la prima cella

                        if not firstcell.has_attr("class"):  # se questa non ha l'attributo class è una materia
                            # adesso che sappiamo che è una materia, estraiamo tutte le celle per ottenere i dati su di essa
                            cells = row.find_all("td")
                            session = cls.SESSIONS[count]  # in base al valore di count sappiamo la sessione che stiamo analizzando
                            flag = False  # variabile sentinella per vedere se la materia che stiamo analizzando è già presente dentro l'array

                            for exam in exams:  # scorriamo tutte le materie fino ad ora inserite (inizialmente, banalmente, saranno 0)
                                if (cells[1]).text == exam.insegnamento:  # se abbiamo trovato la materia nell'array
                                    flag = True  # setto la sentinella a true che indica che la materia era già presente nell'array delle materia dunque dobbiamo solo aggiungere gli appelli della nuova sessione>1

                                    for cell in cells[
                                            3:]:  # dato che la materia è già presente nell'array, i primi 3 valori (id, docenti e nome) non ci interessano
                                        if cell.has_attr("class"):  # se la cella ha l'attributo class allora è un'appello straordinario
                                            exam.append_session("straordinaria", cell.text)
                                        elif cell.text.strip() != "":  # altrimenti è un appello della sessione che stiamo analizzando
                                            exam.append_session(session, cell.text)

                            if not flag:  # se non abbiamo trovato la materia che stiamo analizzando attualmente nell'array delle materie vuol dire che nelle sessioni precedenti non aveva appelli (oppure è la prima sessione)
                                if course == "l-31":
                                    course_name = "Informatica Triennale"
                                elif course == "lm-18":
                                    course_name = "Informatica Magistrale"
                                elif course == "l-35":
                                    course_name = "Matematica Triennale"
                                elif course == "lm-40":
                                    course_name = "Matematica Triennale"

                                # creiamo una nuova istanza di esame da riempire con i dati trovati
                                new_exam = cls(anno=year, cdl=course_name, insegnamento=cells[1].text, docenti=cells[2].text)

                                for cell in cells[3:]:  # come sopra (riga ~29)
                                    if cell.has_attr("class"):
                                        new_exam.append_session("straordinaria", cell.text)
                                    elif cell.text.strip() != "":
                                        new_exam.append_session(session, cell.text)

                                exams.append(new_exam)  # aggiungiamo l'esame trovato alla lista

                        else:  # altrimenti, se ha l'attributo class, è la riga che indica l'anno delle materie successive
                            year = firstcell.b.text  # quindi aggiorniamo la variabile anno con il valore della prima cella della riga

        if delete:
            cls.delete_all()
        cls.bulk_save(exams)  # infine, salviamo tutti gli esami nel database
        logger.info("Exams loaded.")

    @classmethod
    def find(cls, select_sessione: str = "", where_sessione: str = "", where_anno: str = "", where_insegnamento: str = "") -> List['Exam']:
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
        output += "\n*Docenti:* " + self.insegnamento

        for session in self.__class__.SESSIONS:
            if self.get_session(session):
                appeals = str(self.get_session(session))
                #aggiunge un - per separare orario e luogo dell'esame
                appeals = re.sub(r"(?P<ora>([01]?\d|2[0-3]):[0-5][0-9])(?P<parola>\w)", r"\g<ora> - \g<parola>", appeals)
                # separa i vari appelli della sessione
                appeals = re.split(r"[\"'], [\"']", appeals)

                for i, appeal in enumerate(appeals):
                    # rimuove eventuali caratteri [ ' ] rimasti in ogni appello
                    appeals[i] = re.sub(r"[\['\]]", "", appeal)
                    # cattura eventuali link e li rende inoffensivi per il markdown
                    appeals[i] = re.sub(r"(?P<link>https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))",
                                        r"[link](\g<link>)", appeals[i])
                    # rimuove eventuali caratteri * e _ rimasti che non siano nei link
                    appeals[i] = re.sub(r"[*_](?![^(]*[)])", " ", appeals[i])

                if "".join(appeals) != "":
                    output += "\n*" + session.title() + ":*\n" + "\n".join(appeals)

        output += "\n*CDL:* " + self.cdl
        output += "\n*Anno:* " + self.anno + "\n"

        return output
