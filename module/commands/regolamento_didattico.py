# -*- coding: utf-8 -*-
"""/regolamentodidattico command"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from module.shared import check_log

reg_doc_triennale = {
    'Regolamento Didattico 2020/2021': 'http://web.dmi.unict.it/sites/default/files/files/L%2031_Informatica%20AA%202020-21%20all\'albo.pdf',
    'Regolamento Didattico 2019/2020': 'http://web.dmi.unict.it/sites/default/files/files/Regolamento%202019-20%20L%2031_Informatica.pdf',
    'Regolamento Didattico 2018/2019': 'http://web.dmi.unict.it/sites/default/files/files/L%2031%20Informatica(1).pdf',
    'Regolamento Didattico 2017/2018': 'http://web.dmi.unict.it/sites/default/files/files/Regolamento%20L%2031%20Informatica%202017-18.pdf',
    'Regolamento Didattico 2016/2017': 'http://web.dmi.unict.it/sites/default/files/files/Regolamento%20L%2031%20Informatica%202016-17.pdf',
    'Regolamento Didattico 2015/2016': 'http://web.dmi.unict.it/sites/default/files/files/Regolamento%20L%2031%20Informatica%202015-16.pdf',
    'Regolamento Didattico 2014/2015': 'http://web.dmi.unict.it/sites/default/files/files/Didattica%20Programmata%20e%20elenco%20propedeuticit%C3%A0%202014-2015.pdf',
    'Regolamento Didattico 2013/2014': 'http://web.dmi.unict.it/sites/default/files/files/regolamentoDidattico_L31_Informatica_1314.pdf',
    'Regolamento Didattico 2012/2013': 'http://web.dmi.unict.it/sites/default/files/files/regolamentoDidattico_L31_Informatica_1213.pdf',
}

reg_doc_magistrale = {
    'Regolamento Didattico 2020/2021_m': 'http://web.dmi.unict.it/sites/default/files/Regolamento%20Didattico%20LM%2018%202021.pdf',
    'Regolamento Didattico 2019/2020_m': 'http://web.dmi.unict.it/sites/default/files/Regolamento%20Didattico%20LM18%201920_0.pdf',
    'Regolamento Didattico 2018/2019_m': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/Regolamento%20Didattico%20LM18%201819.pdf',
    'Regolamento Didattico 2017/2018_m': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/Regolamento%20Didattico%20LM18%201718.pdf',
    'Regolamento Didattico 2016/2017_m': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/LM%2018%20Informatica_1617.pdf',
    'Regolamento Didattico 2015/2016_m': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/Regolamento%20Didattico%20LM18%201516.pdf'
}

REGOLAMENTI = {'triennale': reg_doc_triennale, 'magistrale': reg_doc_magistrale}


def regolamentodidattico(update: Update, context: CallbackContext):
    """Called by the /regolamentodidattico command.
    Shows a menu from with the user can choose between (triennale | magistrale)

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "regolamentodidattico")
    update.message.reply_text('Scegliere uno dei seguenti corsi:', reply_markup=get_reg_keyboard())

def regolamentodidattico_handler(update: Update, context: CallbackContext):
    """Called by any of the /regolamentodidattico buttons.
    Data can be ( home | triennale | magistrale ).
    Allows the used to navigate between the rulebooks

    Args:
        update: update event
        context: context passed by the handler
    """
    query = update.callback_query
    data = query.data.replace("reg_button_", "")
    if data == "home":
        context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text='Scegliere uno dei seguenti corsi:',
                                  reply_markup=get_reg_keyboard())
    else:
        context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text='Scegliere il regolamento in base al proprio anno di immatricolazione:',
                                  reply_markup=get_reg_keyboard(REGOLAMENTI[data]))


def send_regolamento(update: Update, context: CallbackContext):
    """Called by clicking on a rulebook.
    Sends said rulebook to the user.

    Args:
        update: update event
        context: context passed by the handler
    """
    query = update.callback_query
    data = query.data
    chat_id = update.effective_chat.id
    if data in reg_doc_triennale:
        doc = reg_doc_triennale[data]
    else:
        doc = reg_doc_magistrale[data]

    context.bot.send_document(chat_id=chat_id, document=doc)
    context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text="Ecco il file richiesto:",)


def get_reg_keyboard(reg_doc: dict = None) -> InlineKeyboardMarkup:
    """Called by :meth:`regolamentodidattico` and :meth:`regolamentodidattico_handler`.
    Generates the whole list of rulebooks to append as an InlineKeyboard

    Args:
        reg_doc: rulebooks to show

    Returns:
        list of rulebooks
    """
    if reg_doc is None:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton('Triennale', callback_data='reg_button_triennale'),
            InlineKeyboardButton('Magistrale', callback_data='reg_button_magistrale')
        ]])
    keyboard = [[InlineKeyboardButton(r.replace('_m', ''), callback_data=r)] for r in reg_doc]
    keyboard.append([InlineKeyboardButton('Indietro', callback_data='reg_button_home')])  # back button
    return InlineKeyboardMarkup(keyboard)
