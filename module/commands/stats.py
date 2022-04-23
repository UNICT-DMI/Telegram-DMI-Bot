"""/stats command"""
import os
import warnings
from datetime import date, timedelta
import matplotlib.pyplot as plt
from telegram import Bot, Update
from telegram.ext import CallbackContext
from module.data import DbManager
from module.data.vars import EASTER_EGG

warnings.filterwarnings("ignore", category=UserWarning, message='^Starting a Matplotlib')


def stats(update: Update, context: CallbackContext) -> None:
    """Called by the /stats command.
    Use: /stats [days]
    Shows the history of all the commands requested to the bot in the last 'days'. Defaults to 30.

    Args:
        update: update event
        context: context passed by the handler
    """
    days = 30
    try:
        if context.args and int(context.args[0]) > 0:
            days = int(context.args[0])
    except ValueError:
        pass
    stats_gen(update, context, days)


def stats_tot(update: Update, context: CallbackContext) -> None:
    """Called by the /stats_tot command.
    Shows the history of all the commands requested to the bot

    Args:
        update: update event
        context: context passed by the handler
    """
    stats_gen(update, context)


def stats_gen(update: Update, context: CallbackContext, days: int = 0) -> None:
    """Called by :meth:`stats` or :meth:`stats_tot`.
    Generates the requested stats, both with text and graph

    Args:
        update: update event
        context: context passed by the handler
        days: number of days to consider. Defaults to 0.
    """
    chat_id = update.message.chat_id

    where = f"DateCommand > '{date.today() - timedelta(days=days)}\n'" if days > 0 else ""
    text = f"Record di {days} giorni:\n" if days > 0 else "Record Globale:\n"

    results = DbManager.select_from(select='type, COUNT(chat_id) as n', table_name='stat_list', where=where, group_by="type", order_by="n DESC")
    print(results)
    rows = [row for row in results if row['Type'] not in EASTER_EGG]

    total = 0
    for row in rows:
        text += f"{row['Type']} : {row['n']}\n"
        total += row['n']
    text += f"\nTotale: {total}\nMedia per comando: {round(total/(len(rows) if rows else 1), 2)}"

    context.bot.sendMessage(chat_id=chat_id, text=text)
    send_graph(rows, context.bot, chat_id)


def send_graph(rows: list, bot: Bot, chat_id: int) -> None:
    """Called by :meth:`stats_gen`.
    Generates a graph and sends it to the user

    Args:
        rows: hystory of commands
        bot: telegram bot
        chat_id: id of the chat
    """
    # Consider only the first 10 values
    x = [v['Type'] for v in rows[:10]]
    y = [v['n'] for v in rows[:10]]

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
    with open(f"{chat_id}.png", "rb") as photo:
        bot.send_photo(chat_id=chat_id, photo=photo)
    os.unlink(f"{chat_id}.png")
