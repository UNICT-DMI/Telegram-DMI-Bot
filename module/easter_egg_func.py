# -*- coding: utf-8 -*-
# system
import sqlite3
from datetime import time
from random import randint, choice
from time import sleep
from os import path

# Telegram
from telegram import Update
from telegram.ext import CallbackContext

# utils
from classes.EasterEgg import EasterEgg

# module
from module.shared import check_log, config_map

def smonta_portoni(update: Update, context: CallbackContext) -> None:
    check_log(update, context, "smonta_portoni")
    message_text = EasterEgg.get_smonta_portoni()
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text)

def santino(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if (chat_id == -1001031103640 or chat_id == config_map['dev_group_chatid']):
        check_log(update, context, "santino")
        message_text = EasterEgg.get_santino()
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text)

def bladrim(update: Update, context: CallbackContext) -> None:
    check_log(update, context, "bladrim")
    message_text = EasterEgg.get_bladrim()
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text)

def prof_sticker(update: Update, context: CallbackContext) -> None:
    check_log(update, context, "prof_sticker")
    context.bot.sendSticker(chat_id=update.message.chat_id, sticker=prof_sticker_id())

def prof_sticker_id() -> str:
    db = sqlite3.connect('data/DMI_DB.db')
    i = db.execute("SELECT * FROM 'stickers' ORDER BY RANDOM() LIMIT 1").fetchone()[0]
    db.close()

    return i

def lei_che_ne_pensa_signorina(update: Update, context: CallbackContext) -> None:
    check_log(update, context, "leiCheNePensaSignorina")
    message_text = EasterEgg.get_lei_che_ne_pensa_signorina()
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def tomarchio_schedule(context: CallbackContext) -> None:
    """Called once a day at 00:00 (ROME)
    Schedules the "tomarchio_request" job that will run between 10:00 and 21:00 of the same day
    Also, makes sure the file "data/soldini" exists

    Args:
        context (CallbackContext): context passed by the updater
    """
    if not path.exists("data/soldini"):
        with open("data/soldini", 'w+') as soldini:
            soldini.write("0")
    context.job_queue.run_once(tomarchio_request, when=time(hour=randint(10, 21), minute=randint(0, 59)))


def tomarchio_request(context: CallbackContext) -> None:
    """Called every day between 10:00 and 21:00
    Sends a message to a random chat choosen between the ones listed in "easter_eggs_chat" in the settings.yaml file

    Args:
        context (CallbackContext): context passed by the handler
    """
    chat_id = choice(config_map['easter_eggs_chat'])
    message = context.bot.sendMessage(chat_id=chat_id, text="Hai un euro per il Signor Tomarchio?")
    sleep(30)
    context.bot.deleteMessage(chat_id=chat_id, message_id=message.message_id)

def add_soldino(update: Update, context: CallbackContext) -> None:
    """Called when a user replyes to the "tomarchio_request" message with "Si"
    Adds a "soldino" to the tomarchio balance

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    if update.message.reply_to_message.text == "Hai un euro per il Signor Tomarchio?":
        with open("data/soldini", 'r', encoding="utf8") as in_file:
            soldini = int(in_file.read()) + 1
        with open("data/soldini", 'w', encoding="utf8") as out_file:
            out_file.write(str(soldini))


def tomarchio_balance(update: Update, context: CallbackContext) -> None:
    """Called with the /tomarchio command
    Shows the tomarchio balance

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    check_log(update, context, "tomarchioBalance")
    with open("data/soldini", 'r', encoding="utf8") as in_file:
        soldini = int(in_file.read()) + 1
    message_text = "Tomarchio ha {} euro per il caffè.".format(soldini)
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text)
