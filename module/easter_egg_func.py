# -*- coding: utf-8 -*-
"""Nobody knows what those functions do"""
import sqlite3
from telegram import Update
from telegram.ext import CallbackContext
from module.data import EasterEgg
from module.shared import check_log, config_map


def smonta_portoni(update: Update, context: CallbackContext):
    check_log(update, "smonta_portoni")
    message_text = EasterEgg.get_smonta_portoni()
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def santino(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id in (-1001031103640, config_map['dev_group_chatid']):
        check_log(update, "santino")
        message_text = EasterEgg.get_santino()
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def bladrim(update: Update, context: CallbackContext):
    check_log(update, "bladrim")
    message_text = EasterEgg.get_bladrim()
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def prof_sticker(update: Update, context: CallbackContext):
    check_log(update, "prof_sticker")
    context.bot.sendSticker(chat_id=update.message.chat_id, sticker=prof_sticker_id())


def prof_sticker_id() -> str:
    db = sqlite3.connect('data/DMI_DB.db')
    i = db.execute("SELECT * FROM 'stickers' ORDER BY RANDOM() LIMIT 1").fetchone()[0]
    db.close()
    return i


def lei_che_ne_pensa_signorina(update: Update, context: CallbackContext):
    check_log(update, "leiCheNePensaSignorina")
    message_text = EasterEgg.get_lei_che_ne_pensa_signorina()
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def uni_bandita(update: Update, context: CallbackContext):
    check_log(update, "uni_bandita")
    message_text = EasterEgg.get_uni_bandita()
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode="Markdown",
                            disable_web_page_preview=True)
