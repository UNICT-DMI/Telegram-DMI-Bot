from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

import random

from module.shared import check_log, CUSicon, read_md, AULARIO, CLOUD

def help(update: Update, context: CallbackContext) -> None:
    check_log(update, context, "help")
    chat_id = update.message.chat_id
    
    message_text = "@DMI_Bot risponde ai seguenti comandi:"

    keyboard = [[]]
    keyboard.append([InlineKeyboardButton(" ~ Dipartimento e CdL ~ ", callback_data="NONE")])

    keyboard.append([
        InlineKeyboardButton("📖 Esami (link)",         callback_data="md_esami_link"),
        InlineKeyboardButton(AULARIO,                   callback_data="sm_aulario"),
    ])

    keyboard.append([
        InlineKeyboardButton("📘 Orari lezioni (link)",    callback_data="md_lezioni_link"),
        InlineKeyboardButton("👨‍🏫 Info Professori",    callback_data="md_professori")
    ])

    keyboard.append([
        InlineKeyboardButton("Regolamento Didattico", callback_data="regolamentodidattico_button")
    ])

    keyboard.append([
        InlineKeyboardButton("👥 Rappresentanti",                       callback_data="sm_rapp_menu"),
        InlineKeyboardButton("📚 Biblioteca",                           callback_data="md_biblioteca"),
        InlineKeyboardButton("📊 Gruppi",				   callback_data="md_gruppi"),
    ])

    keyboard.append([
        InlineKeyboardButton(CUSicon[random.randint(0, 5)] + " CUS",    callback_data="md_cus"),
        InlineKeyboardButton(CLOUD,                                     callback_data="md_cloud")
    ])

    keyboard.append([InlineKeyboardButton(" ~ Segreteria orari e contatti ~ ", callback_data="NONE")])

    keyboard.append([
        InlineKeyboardButton("Seg. Didattica",  callback_data="md_sdidattica"),
        InlineKeyboardButton("Seg. Studenti",   callback_data="md_sstudenti"),
        InlineKeyboardButton("CEA",             callback_data="md_cea")
    ])

    keyboard.append([InlineKeyboardButton(" ~ ERSU orari e contatti ~ ", callback_data="NONE")])

    keyboard.append([
        InlineKeyboardButton("ERSU",          callback_data="md_ersu"),
        InlineKeyboardButton("Ufficio ERSU",  callback_data="md_ufficioersu"),
        InlineKeyboardButton("URP",           callback_data="md_urp")
    ])

    keyboard.append([InlineKeyboardButton(" ~ Bot e varie ~ ", callback_data="NONE")])

    keyboard.append([
        InlineKeyboardButton("📂 Drive",             callback_data="md_drive"),
        InlineKeyboardButton("📂 GitLab",            callback_data="md_gitlab")
    ])

    keyboard.append([InlineKeyboardButton(" ~ Progetti e Riconoscimenti ~ ", callback_data="NONE")])
    
    keyboard.append([
        InlineKeyboardButton("📈 Opis Manager",      callback_data="md_opismanager"),
        InlineKeyboardButton("Contributors",         callback_data="md_contributors")
    ])


    keyboard.append([
        InlineKeyboardButton("Tutti i comandi", callback_data="md_help"),
        InlineKeyboardButton("Chiudi",          callback_data="exit_cmd")
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.sendMessage(chat_id=chat_id, text=message_text, reply_markup=reply_markup)

def rapp_menu(update: Update, context: CallbackContext, chat_id, message_id: int) -> None:
    
    message_text = "Quali rappresentanti vuoi contattare?"

    keyboard = [[]]
    keyboard.append(
        [
            InlineKeyboardButton("Rapp. DMI",         callback_data="md_rappresentanti_dmi"),
            InlineKeyboardButton("Rapp. Informatica", callback_data="md_rappresentanti_informatica"),
            InlineKeyboardButton("Rapp. Matematica",  callback_data="md_rappresentanti_matematica"),
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)

def exit_cmd() -> str:
    output = "."
    return output
