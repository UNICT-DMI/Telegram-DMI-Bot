# -*- coding: utf-8 -*-
"""Professor class"""
import logging
from typing import List
import bs4
import requests
from module.data.db_manager import DbManager
from module.data.scrapable import Scrapable

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class Professor(Scrapable):
    """Professor

    Base:
        Scrapable (:class:`Scrapable`): base class

    Attributes:
        ID (:class:`int`): primary key of the table
        ruolo (:class:`str`): role of the professor
        nome (:class:`str`): name of the professor
        cognome (:class:`str`): surname of the professor
        scheda_dmi (:class:`str`): web-page about the professor
        fax (:class:`str`): fax of the professor
        telefono (:class:`str`): phone number of the professor
        email (:class:`str`): e-mail of the professor
        ufficio (:class:`str`): which office belogs to the professor
        sito (:class:`str`): orcid page of the professor
    """
    URL_PROF = "http://web.dmi.unict.it/docenti"

    def __init__(self,
                 ID: int = -1,
                 ruolo: str = "",
                 nome: str = "",
                 cognome: str = "",
                 scheda_dmi: str = "",
                 fax: str = "",
                 telefono: str = "",
                 email: str = "",
                 ufficio: str = "",
                 sito: str = ""):
        self.ID = ID
        self.ruolo = ruolo
        self.nome = nome
        self.cognome = cognome
        self.scheda_dmi = scheda_dmi
        self.fax = fax
        self.telefono = telefono
        self.email = email
        self.ufficio = ufficio
        self.sito = sito

    @property
    def table(self) -> str:
        """:class:`str`: name of the database table that will store this Lesson"""
        return "professors"

    @property
    def columns(self) -> tuple:
        """:class:`tuple`: tuple of column names of the database table that will store this Professor"""
        return ("ID", "ruolo", "nome", "cognome", "scheda_dmi", "fax", "telefono", "email", "ufficio", "sito")

    @classmethod
    def scrape(cls, delete=False):
        """Scrapes all the professors and stores them in the database

        Args:
            delete (:class:`bool`, optional): whether the table contents should be deleted first. Defaults to False.
        """
        if delete:
            cls.delete_all()

        professors = []
        count = 0

        contract = False
        mother_tongue = False

        source = requests.get(cls.URL_PROF).text
        soup = bs4.BeautifulSoup(source, "html.parser")
        table = soup.find(id="persone")

        for link in table.find_all("a"):
            if not link.has_attr("name"):
                href = link['href']
                surname = link.text.split(" ")[0]
                name = ""

                for i in range(len(link.text.split(" ")) - 1):
                    name += link.text.split(" ")[i + 1] + " "

                if contract:
                    role = "Contratto"
                elif mother_tongue:
                    role = "Lettore madrelingua"
                else:
                    role = link.parent.next_sibling.text.split(" ")[1] if len(
                        link.parent.next_sibling.text.split(" ")) > 1 else link.parent.next_sibling.text

                if link.parent.parent.next_sibling.next_sibling is not None\
                    and link.parent.parent.next_sibling.next_sibling.find("td").find("b") is not None:
                    contract = False
                    mother_tongue = True

                    if not contract:
                        contract = True
                        mother_tongue = False

                count += 1
                professor = cls(ID=count, ruolo=role.title(), nome=name, cognome=surname, scheda_dmi=f"http://web.dmi.unict.it{href}")

                source = requests.get(professor.scheda_dmi).text
                soup = bs4.BeautifulSoup(source, "html.parser")
                div = soup.find(id="anagrafica")
                for bi in div.find_all("b"):
                    if bi.text == "Ufficio:":
                        professor.ufficio = bi.next_sibling
                    elif bi.text == "Email:":
                        professor.email = bi.next_sibling.next_sibling.text
                    elif bi.text == "Sito web:":
                        professor.sito = bi.next_sibling.next_sibling.text
                    elif bi.text == "Telefono:":
                        professor.telefono = bi.next_sibling
                    elif bi.text == "Fax:":
                        professor.fax = bi.next_sibling

                professors.append(professor)

        cls.bulk_save(professors)
        logger.info("Professors loaded.")

    @classmethod
    def find(cls, where_name: str) -> List['Professor']:
        """Produces a list of professors from the database, based on the provided parametes

        Returns:
            :class:`List[Professor]`: result of the query on the database
        """
        db_results = DbManager.select_from(table_name=cls().table,
                                           where="nome LIKE ? OR cognome LIKE ?",
                                           where_args=(f'%{where_name}%', f'%{where_name}%'))
        return cls._query_result_initializer(db_results)

    @classmethod
    def find_all(cls) -> List['Professor']:
        """Finds all the professors present in the database

        Returns:
            :class:`List['Professor']`: list of all the professors
        """
        return super().find_all()

    def __repr__(self):
        return f"Professor: {self.__dict__}"

    def __str__(self):
        string = f"*Ruolo:* {self.ruolo}\n"\
                f"*Cognome:* {self.cognome}\n"\
                f"*Nome:* {self.nome}\n"
        if self.email:
            string += f"*Indirizzo email:* {self.email}\n"
        if self.scheda_dmi:
            string += f"*Scheda DMI:* {self.scheda_dmi}\n"
        if self.sito:
            string += f"*Sito web:* {self.sito}\n"
        if self.ufficio:
            string += f"*Ufficio:* {self.ufficio}\n"
        if self.telefono:
            string += f"*Telefono:* {self.telefono}\n"
        if self.fax:
            string += f"*Fax:* {self.fax}\n"
        return string
