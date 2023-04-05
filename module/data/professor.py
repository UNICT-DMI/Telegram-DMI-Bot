# -*- coding: utf-8 -*-
"""Professor class"""
import logging
from typing import List
import bs4
import requests
from module.data.db_manager import DbManager
from module.data.scrapable import Scrapable
from telegram.utils.helpers import escape_markdown

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def em(text):
    """
    Alias for `escape_markdown` function
    """
    return escape_markdown(text, version=2)


# pylint: disable=too-many-instance-attributes
class Professor(Scrapable):
    """Professor

    Attributes:
        ID (:class:`int`): primary key of the table
        ruolo (:class:`str`): role of the professor
        nome (:class:`str`): name of the professor
        scheda_dmi (:class:`str`): web-page about the professor
        fax (:class:`str`): fax of the professor
        telefono (:class:`str`): phone number of the professor
        email (:class:`str`): e-mail of the professor
        ufficio (:class:`str`): which office belogs to the professor
        sito (:class:`str`): orcid page of the professor
        photo_id (:class:`str`): photo id of the professor's page
    """
    URL_PROF = "http://web.dmi.unict.it/docenti"

    # pylint: disable=too-many-arguments
    def __init__(self,
                 ID: int = -1,
                 ruolo: str = "",
                 nome: str = "",
                 scheda_dmi: str = "",
                 fax: str = "",
                 telefono: str = "",
                 email: str = "",
                 ufficio: str = "",
                 sito: str = "",
                 photo_id: str = ""):
        self.ID = ID
        self.ruolo = ruolo
        self.nome = nome
        self.scheda_dmi = scheda_dmi
        self.fax = fax
        self.telefono = telefono
        self.email = email
        self.ufficio = ufficio
        self.sito = sito
        self.photo_id = photo_id

    @property
    def table(self) -> str:
        """name of the database table that will store this Lesson"""
        return "professors"

    @property
    def columns(self) -> tuple:
        """tuple of column names of the database table that will store this Professor"""
        return ("ID", "ruolo", "nome", "scheda_dmi", "fax", "telefono", "email", "ufficio", "sito", "photo_id")

    @classmethod
    def scrape(cls, delete: bool = False):
        """Scrapes all the professors and stores them in the database

        Args:
            delete: whether the table contents should be deleted first. Defaults to False.
        """
        professors = []
        count = 0

        contract = False
        mother_tongue = False

        source = requests.get(cls.URL_PROF, timeout=10).text
        soup = bs4.BeautifulSoup(source, "html.parser")
        table = soup.find(id="persone")

        for link in table.find_all("a"):
            if not link.has_attr("name"):
                href = link['href']
                name = link.text

                if contract:
                    role = "Contratto"
                elif mother_tongue:
                    role = "Lettore madrelingua"
                else:
                    role = link.parent.next_sibling.text.split(" ")[1] if len(
                        link.parent.next_sibling.text.split(" ")) > 1 else link.parent.next_sibling.text

                if link.parent.parent.next_sibling.next_sibling is not None \
                        and link.parent.parent.next_sibling.next_sibling.find("td").find("b") is not None:
                    contract = False
                    mother_tongue = True

                    if not contract:
                        contract = True
                        mother_tongue = False

                count += 1
                professor = cls(ID=count, ruolo=role.title(), nome=name, scheda_dmi=f"http://web.dmi.unict.it{href}")

                source = requests.get(professor.scheda_dmi, timeout=10).text
                soup = bs4.BeautifulSoup(source, "html.parser")
                div = soup.find("div", {"class": "card-body"})
                if div is None:
                    continue
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
                if soup.find("div", {"class": "avatar size-xxl size-xxxl"}):
                    professor.photo_id = soup.find("div", {"class": "avatar size-xxl size-xxxl"}).find("img").get("src")
                else:
                    professor.photo_id = "Non presente"

                professors.append(professor)

        if delete:
            cls.delete_all()
        cls.bulk_save(professors)
        logger.info("Professors loaded.")

    @classmethod
    def find(cls, where_name: str) -> List['Professor']:
        """Produces a list of professors from the database, based on the provided parametes

        Args:
            where_name: specifies the name of the professor

        Returns:
            result of the query on the database
        """
        where = " AND ".join(("nome LIKE ?" for name in where_name))
        where_args = tuple(f'%{name}%' for name in where_name)

        db_results = DbManager.select_from(table_name=cls().table,
                                           where=where,
                                           where_args=where_args)
        return cls._query_result_initializer(db_results)

    @classmethod
    def find_all(cls) -> List['Professor']:
        """Finds all the professors present in the database

        Returns:
            list of all the professors
        """
        return super().find_all()

    def __repr__(self):
        return f"Professor: {self.__dict__}"

    def __str__(self):
        string = f"*Ruolo:* {em(self.ruolo)}\n" \
                 f"*Nome:* {em(self.nome)}\n"
        if self.email:
            string += f"*Indirizzo email:* {em(self.email)}\n"
        if self.scheda_dmi:
            string += f"*Scheda DMI:* {em(self.scheda_dmi)}\n"
        if self.sito:
            string += f"*Sito web:* {em(self.sito)}\n"
        if self.ufficio:
            string += f"*Ufficio:* {em(self.ufficio)}\n"
        if self.telefono:
            string += f"*Telefono:* {em(self.telefono)}\n"
        if self.fax:
            string += f"*Fax:* {em(self.fax)}\n"
        if self.photo_id:
            string += f"*ID Foto:* {em(self.photo_id)}\n"
        return string
