import bs4
import requests
import json
import logging
import sqlite3

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_giorno(giorno):
    if giorno == "LUN":
        return 1
    elif giorno == "MAR":
        return 2
    elif giorno == "MER":
        return 3
    elif giorno == "GIO":
        return 4
    elif giorno == "VEN":
        return 5
    else:
        return 0

def scrape_lessons(year_exams):
    ids = ["l-31","l-35","lm-18","lm-40"]
    items = []
    for id_ in ids:
        urls = [
            "http://web.dmi.unict.it/corsi/"+str(id_)+"/orario-lezioni?semestre=1&aa="+year_exams,
            "http://web.dmi.unict.it/corsi/"+str(id_)+"/orario-lezioni?semestre=2&aa="+year_exams
        ]
        for url in urls:
            sorgente = requests.get(url).text
            soup = bs4.BeautifulSoup(sorgente, "html.parser")

            if soup.find('b',id='attivo').text[0] == 'S':
                semestre = 2
            elif soup.find('b',id='attivo').text[0] == 'P':
                semestre = 1

            table = soup.find('table',id='tbl_small_font')
            tr_all =  table.find_all('tr')

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
                                giorno = get_giorno(orario[0:3])
                                orario = orario.replace(orario[0:3],'') #GIORNO
                                ora_inizio = orario[1:6] #ORA INIZIO
                                ora_fine = orario[7:12] #ORA FINE
                                orario = orario.replace(ora_inizio + "-" + ora_fine,'')
                                aula = orario[2:]

                                items.append({
                                 "nome": td_all[0].text,
                                 "giorno_settimana": str(giorno),
                                 "ora_inizio": ora_inizio,
                                 "ora_fine": ora_fine,
                                 "aula": str(aula),
                                 "anno": str(anno),
                                 "semestre": str(semestre)
                                })

    columns = "`" + "`, `".join(items[0].keys()) + "`"

    values = ""
    for i in items:
    	values += '("'+'", "'.join(str(v) for v in i.values())+'"),'
    values = values[:-1]

    query = "INSERT INTO lessons ({}) VALUES {}".format(columns, values)

    conn = sqlite3.connect('data/DMI_DB.db')
    conn.execute('DELETE FROM `lessons`;') # TRUNCATE lessons
    conn.execute(query)
    conn.commit()
    conn.close()

    logger.info("Lessons loaded.")
