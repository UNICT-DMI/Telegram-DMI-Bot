# Telegram
from telegram import Update, Bot
from telegram.ext import CallbackContext

# System libraries
import sqlite3
import os
from datetime import date, timedelta
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore", category=UserWarning, message='^Starting a Matplotlib')

EASTER_EGG = ("leiCheNePensaSignorina", "smonta_portoni", "santino", "bladrim", "prof_sticker")

def stats(update: Update, context: CallbackContext):
    days = 30
    if context.args and int(context.args[0]) > 0:
        days = int(context.args[0])
    stats_gen(update, context, days)

def stats_gen(update: Update, context: CallbackContext, days):
    conn = sqlite3.connect('data/DMI_DB.db')
    chat_id = update.message.chat_id
    text = ""

    if days == 0:
        text += "Record Globale:\n"
        query = "SELECT Type, COUNT(chat_id) as n FROM stat_list GROUP BY Type ORDER BY n DESC;"
    else:
        text += "Record di "+str(days)+" giorni:\n"
        query = "SELECT Type, COUNT(chat_id) as n FROM stat_list WHERE DateCommand > '"+ str(date.today()-timedelta(days=days)) + "' GROUP BY Type ORDER BY n DESC;"

    rows = [row for row in conn.execute(query).fetchall() if row[0] not in EASTER_EGG]
    conn.close()

    total = 0
    for row in rows:
        text += f"{row[1]} : {row[0]}\n"
        total+= row[1]
    text += f"\nTotale: {total}\nMedia per comando: {round(total/len(rows), 2)}"

    context.bot.sendMessage(chat_id=chat_id, text=text)
    send_graph(rows, context.bot, chat_id)

def stats_tot(update: Update, context: CallbackContext):
    stats_gen(update, context, 0)

# Create the graph and send it to the user
def send_graph(rows: list, bot: Bot, chat_id: int):
    # Consider only the first 10 values
    x = [v[0] for v in rows[:10]]
    y = [v[1] for v in rows[:10]]

    _, ax = plt.subplots()

    # Set the graphic's labels
    ax.bar(x, y, align='center')
    ax.set_title('Statistiche utilizzo comandi')
    ax.set_ylabel('Utilizzi')
    ax.set_xlabel('Comandi')

    # Fix the graphic's aspect and save it as an image
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='center', fontsize='xx-small')
    plt.tight_layout()
    plt.savefig(str(chat_id))

    # Send the graph to the user and delete the file
    with open(str(chat_id) + ".png", "rb") as photo:
        bot.send_photo(chat_id=chat_id, photo=photo)
    os.unlink(str(chat_id) + ".png")
