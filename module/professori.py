# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import CallbackContext
from module.shared import check_log, send_message

import json
import sqlite3

def prof(update: Update, context: CallbackContext):
    check_log(update, context, "prof")
    message_text = prof_cmd(context.args)
    if len(message_text) > 4096:
        send_message(update, context, message_text)
    else:
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')

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
            rows = conn.execute("SELECT * FROM professors WHERE Nome LIKE '%" + i + "%' OR Cognome LIKE '%" + i + "%' ").fetchall()
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
