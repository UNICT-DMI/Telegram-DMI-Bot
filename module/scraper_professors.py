# -*- coding: utf-8 -*-

import bs4
import requests
import json
import sqlite3
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def get_anagraphic(link):
    dic = {"ufficio": "", "email": "", "sito": "", "telefono": "", "fax": ""}
    source = requests.get("http://web.dmi.unict.it"+str(link)).text
    soup = bs4.BeautifulSoup(source, "html.parser")
    div = soup.find(id="anagrafica")
    for bi in div.find_all("b"):
        if bi.text == "Ufficio:":
            dic['ufficio'] = bi.next_sibling
        elif bi.text == "Email:":
            dic['email'] = bi.next_sibling.next_sibling.text
        elif bi.text == "Sito web:":
            dic['sito'] = bi.next_sibling.next_sibling.text
        elif bi.text == "Telefono:":
            dic['telefono'] = bi.next_sibling
        elif bi.text == "Fax:":
            dic['fax'] = bi.next_sibling
    return dic


def scrape_prof():
    url_prof = "http://web.dmi.unict.it/docenti"

    items = []
    count = 0

    contract = False
    mother_tongue = False

    href = ""
    surname = ""
    name = ""
    role = ""

    source = requests.get(url_prof).text
    soup = bs4.BeautifulSoup(source, "html.parser")
    table = soup.find(id="persone")

    for link in table.find_all("a"):
        if not link.has_attr("name"):
            href = link['href']
            surname = link.text.split(" ")[0]
            name = ""

            for i in range(len(link.text.split(" "))-1):
                name += link.text.split(" ")[i+1] + " "

            if contract:
                role = "Contratto"
            elif mother_tongue:
                role = "Lettore madrelingua"
            else:
                role = link.parent.next_sibling.text.split(" ")[1] if len(link.parent.next_sibling.text.split(" ")) > 1 else link.parent.next_sibling.text

            if link.parent.parent.next_sibling.next_sibling != None and link.parent.parent.next_sibling.next_sibling.find("td").find("b") != None:
                contract = False
                mother_tongue = True

                if not contract:
                    contract = True
                    mother_tongue = False

            count += 1

            anagraphic = get_anagraphic(href)
            items.append({
                "ID": count,
                "Ruolo": role.title(),
                "Nome": name,
                "Cognome": surname,
                "Scheda DMI": "http://web.dmi.unict.it" + href,
                "Fax": anagraphic['fax'],
                "Telefono": anagraphic['telefono'],
                "Email": anagraphic['email'],
                "Ufficio" : anagraphic['ufficio'],
                "Sito" : anagraphic['sito']
            })

    columns = "`" + "`, `".join(items[0].keys()) + "`"

    values = ""
    for i in items:
    	values += '("'+'", "'.join(str(v).replace('"', '') for v in i.values())+'"),'
    values = values[:-1]

    query = "INSERT INTO professors ({}) VALUES {}".format(columns, values)

    conn = sqlite3.connect('data/DMI_DB.db')
    conn.execute('DELETE FROM `professors`;') # TRUNCATE professors
    conn.execute(query)
    conn.commit()
    conn.close()

    logger.info("Professors loaded.")
