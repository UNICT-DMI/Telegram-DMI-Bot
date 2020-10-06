# -*- coding: utf-8 -*-

import json
import sqlite3

def prof_output(prof):
    output = "*Ruolo:* " + prof[1] + "\n"
    output += "*Cognome:* " + prof[3] + "\n"
    output += "*Nome:* " + prof[2] + "\n"

    if prof[7] != "":
        output += "*Indirizzo email:* " + prof[7] + "\n"
    if prof[4] != "":
        output += "*Scheda DMI:* " + prof[4] + "\n"
    if prof[9] != "":
        output += "*Sito web:* " + prof[9] + "\n"
    if prof[8] != "":
        output += "*Ufficio:* " + prof[8] + "\n"
    if prof[6] != "":
        output += "*Telefono:* " + prof[6] + "\n"
    if prof[5] != "":
        output += "*Fax:* " + prof[5] + "\n"
    return output

def prof_cmd(profs):

    if profs:
        output = set()
        profs = [x.lower() for x in profs if len(x) > 3]
        conn = sqlite3.connect('data/DMI_DB.db')

        professors = []
        for i in profs:
            rows = conn.execute("SELECT * FROM professors WHERE Nome LIKE ? OR Cognome LIKE ?",  (('%' + i + '%'), ('%' + i + '%'))).fetchall()
            professors += rows

        for prof in professors:
            output.add(prof_output(prof))

        if len(output):
            output_str = '\n'.join(list(output))
        else:
            output_str = "Nessun risultato trovato :(\n"
        conn.close()
    else:
        output_str = "La sintassi del comando è: /prof <nomeprofessore>\n"

    return output_str
