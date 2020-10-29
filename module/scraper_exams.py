# -*- coding: utf-8 -*-

import bs4
import requests
import json
import logging
import sqlite3
from time import localtime, strftime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_exams(year_exams, delete= False):
	url_exams = {
		"l-31":	[ # Informatica Triennale
			"http://web.dmi.unict.it/corsi/l-31/esami?sessione=1&aa="+year_exams,
			"http://web.dmi.unict.it/corsi/l-31/esami?sessione=2&aa="+year_exams,
			"http://web.dmi.unict.it/corsi/l-31/esami?sessione=3&aa="+year_exams
		],
		"lm-18": [ # Informatica Magistrale
			"http://web.dmi.unict.it/corsi/lm-18/esami?sessione=1&aa="+year_exams,
			"http://web.dmi.unict.it/corsi/lm-18/esami?sessione=2&aa="+year_exams,
			"http://web.dmi.unict.it/corsi/lm-18/esami?sessione=3&aa="+year_exams
		],
		"l-35": [ # Matematica Triennale
			"http://web.dmi.unict.it/corsi/l-35/esami?sessione=1&aa="+year_exams,
			"http://web.dmi.unict.it/corsi/l-35/esami?sessione=2&aa="+year_exams,
			"http://web.dmi.unict.it/corsi/l-35/esami?sessione=3&aa="+year_exams
		],
		"lm-40": [ # Matematica Magistrale
			"http://web.dmi.unict.it/corsi/lm-40/esami?sessione=1&aa="+year_exams,
			"http://web.dmi.unict.it/corsi/lm-40/esami?sessione=2&aa="+year_exams,
			"http://web.dmi.unict.it/corsi/lm-40/esami?sessione=3&aa="+year_exams
		]
	}

	courses = ["l-31", "lm-18", "l-35", "lm-40"]
	session_array = ["prima", "seconda", "terza"]
	items = []
	year = ""

	for course in courses:
		for count, url in enumerate(url_exams[course]):
			source = requests.get(url).text
			soup = bs4.BeautifulSoup(source, "html.parser")
			table = soup.find(id="tbl_small_font")
			rows = table.find_all("tr") # e dalla tabella estraiamo l'array con tutte le righe

			for row in rows: # e scorriamo riga per riga

				if not row.has_attr("class"): # se non ha l'attributo class potrebbe essere una materia oppure l'anno (altrimenti è la riga delle informazioni che non ci interessa)
					firstcell = row.find("td") 	# estraiamo la prima cella

					if not firstcell.has_attr("class"): # se questa non ha l'attributo class è una materia
						cells = row.find_all("td") 				# adesso che sappiamo che è una materia, estraiamo tutte le celle per ottenere i dati su di essa
						session = session_array[count] 		# in base al valore di count sappiamo la sessione che stiamo analizzando
						flag = False 										  # variabile sentinella per vedere se la materia che stiamo analizzando è già presente dentro l'array

						for item in items: 														# scorriamo tutte le materie fino ad ora inserite (inizialmente, banalmente, saranno 0)
							if (cells[1]).text == item["insegnamento"]: # se abbiamo trovato la materia nell'array
								flag = True 															# setto la sentinella a true che indica che la materia era già presente nell'array delle materia dunque dobbiamo solo aggiungere gli appelli della nuova sessione>1

								for cell in cells[3:]: 												# dato che la materia è già presente nell'array, i primi 3 valori (id, docenti e nome) non ci interessano
									if (cell.has_attr("class")): 								# se la cella ha l'attributo class allora è un'appello straordinario
										(item["straordinaria"]).append(cell.text)
									elif (cell.text.strip() != ""): 						# altrimenti è un appello della sessione che stiamo analizzando
										(item[session]).append(cell.text)

						if not flag: # se non abbiamo trovato la materia che stiamo analizzando attualmente nell'array delle materie vuol dire che nelle sessioni precedenti non aveva appelli (oppure è la prima sessione)
							if(course == "l-31"):
								course_name = "Informatica Triennale"
							elif(course == "lm-18"):
								course_name = "Informatica Magistrale"
							elif(course == "l-35"):
								course_name = "Matematica Triennale"
							elif(course == "lm-40"):
								course_name = "Matematica Triennale"

							new_item = {"insegnamento" : "", "docenti" : "", "prima" : [], "seconda" : [], "terza" : [], "straordinaria" : [], "anno" : year, "cdl" : course_name} #creiamo l'oggetto della nuova materia
							new_item["insegnamento"] = cells[1].text
							new_item["docenti"] = cells[2].text

							for cell in cells[3:]: # come sopra (riga ~29)
								if(cell.has_attr("class")):
									(new_item["straordinaria"]).append(cell.text)
								elif(cell.text.strip() != ""):
									(new_item[session]).append(cell.text)

							items.append(new_item) # infine, aggiungiamo la nuova materia all'array delle materie

					else: 										# altrimenti, se ha l'attributo class, è la riga che indica l'anno delle materie successive
						year = firstcell.b.text # quindi aggiorniamo la variabile anno con il valore della prima cella della riga

	columns = "`" + "`, `".join(items[0].keys()) + "`"

	values = ""
	for i in items:
		values += '("'+'", "'.join(str(v).replace("\"", "'") for v in i.values())+'"),' # serve ad evitare errori nella formazione della query, che nascono dalla presenza di " nel bel mezzo di un valore
	values = values[:-1]

	query = "INSERT INTO exams ({}) VALUES {}".format(columns, values)

	conn = sqlite3.connect('data/DMI_DB.db')
	if(delete):
		conn.execute('DELETE FROM `exams`;') # TRUNCATE professors
	try:
		conn.execute(query)
		conn.commit()
	except:
		logger.error("The exams query could not be executed")

	conn.close()

	logger.info("Exams loaded.")
