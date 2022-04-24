# -*- coding: utf-8 -*-
"""/regolamentodidattico command"""
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import CallbackContext
from module.shared import check_log
from module.commands.help import help_cmd
from module.data.vars import TEXT_IDS
from module.utils.multi_lang_utils import get_locale

reg_doc_triennale_L31 = {
    'Regolamento Didattico 2021/2022_L31': 'http://web.dmi.unict.it/sites/default/files/files/L%2031_%20Informatica.pdf',
    'Regolamento Didattico 2020/2021_L31': 'http://web.dmi.unict.it/sites/default/files/files/L%2031_Informatica%20AA%202020-21%20all\'albo.pdf',
    'Regolamento Didattico 2019/2020_L31': 'http://web.dmi.unict.it/sites/default/files/files/Regolamento%202019-20%20L%2031_Informatica.pdf',
    'Regolamento Didattico 2018/2019_L31': 'http://web.dmi.unict.it/sites/default/files/files/L%2031%20Informatica(1).pdf',
    'Regolamento Didattico 2017/2018_L31': 'http://web.dmi.unict.it/sites/default/files/files/Regolamento%20L%2031%20Informatica%202017-18.pdf',
    'Regolamento Didattico 2016/2017_L31': 'http://web.dmi.unict.it/sites/default/files/files/Regolamento%20L%2031%20Informatica%202016-17.pdf',
    'Regolamento Didattico 2015/2016_L31': 'http://web.dmi.unict.it/sites/default/files/files/Regolamento%20L%2031%20Informatica%202015-16.pdf',
    'Regolamento Didattico 2014/2015_L31': 'http://web.dmi.unict.it/sites/default/files/files/Didattica%20Programmata%20e%20elenco%20propedeuticit%C3%A0%202014-2015.pdf',
    'Regolamento Didattico 2013/2014_L31': 'http://web.dmi.unict.it/sites/default/files/files/regolamentoDidattico_L31_Informatica_1314.pdf',
    'Regolamento Didattico 2012/2013_L31': 'http://web.dmi.unict.it/sites/default/files/files/regolamentoDidattico_L31_Informatica_1213.pdf',
}

reg_doc_magistrale_LM18 = {
    'Regolamento Didattico 2021/2022_LM18': 'http://web.dmi.unict.it/sites/default/files/Regolamento%20Didattico%20LM%2018%202122.pdf',
    'Regolamento Didattico 2020/2021_LM18': 'http://web.dmi.unict.it/sites/default/files/Regolamento%20Didattico%20LM%2018%202021.pdf',
    'Regolamento Didattico 2019/2020_LM18': 'http://web.dmi.unict.it/sites/default/files/Regolamento%20Didattico%20LM18%201920_0.pdf',
    'Regolamento Didattico 2018/2019_LM18': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/Regolamento%20Didattico%20LM18%201819.pdf',
    'Regolamento Didattico 2017/2018_LM18': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/Regolamento%20Didattico%20LM18%201718.pdf',
    'Regolamento Didattico 2016/2017_LM18': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/LM%2018%20Informatica_1617.pdf',
    'Regolamento Didattico 2015/2016_LM18': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/Regolamento%20Didattico%20LM18%201516.pdf'
}

reg_doc_triennale_L35 = {
    'Regolamento Didattico 2021/2022_L35': 'http://web.dmi.unict.it/sites/default/files/files/L%2035_Matematica21_22_rivisto.pdf',
    'Regolamento Didattico 2020/2021_L35': 'http://web.dmi.unict.it/sites/default/files/files/L%2035_Matematica_2020_21approvato.pdf',
    'Regolamento Didattico 2019/2020_L35': 'http://web.dmi.unict.it/sites/default/files/files/L%2035_Matematica.pdf',
    'Regolamento Didattico 2018/2019_L35': 'http://web.dmi.unict.it/sites/default/files/files/Regol%20L35_1819%20approvato%20Senato.pdf',
    'Regolamento Didattico 2017/2018_L35': 'http://web.dmi.unict.it/sites/default/files/files/L%2035%20ufficiale1718.pdf',
    'Regolamento Didattico 2016/2017_L35': 'http://web.dmi.unict.it/sites/default/files/files/regolamento1617pubbldallAteneo.pdf',
}

reg_doc_magistrale_LM40 = {
    'Regolamento Didattico 2021/2022_LM40': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/Regolamento%20Didattico%20LM%2040%20senato%20approved%20.pdf',
    'Regolamento Didattico 2020/2021_LM40': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/LM%2040_Matematica%202020-21%20approvato%20Senato.pdf',
    'Regolamento Didattico 2019/2020_LM40': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/LM%2040_Matematica%2019-20%20approvato%20senato.pdf',
    'Regolamento Didattico 2018/2019_LM40': 'http://web.dmi.unict.it/sites/default/files/documenti_sito/LM%2040%20Matematica%202018-19%20approvato%20senato.pdf',
}

REGOLAMENTI = {
    'triennale_L31': reg_doc_triennale_L31,
    'magistrale_LM18': reg_doc_magistrale_LM18,
    'triennale_L35': reg_doc_triennale_L35,
    'magistrale_LM40': reg_doc_magistrale_LM40
}


def regolamentodidattico(update: Update, context: CallbackContext) -> None:
    """Called by the /regolamentodidattico command.
    Shows a menu from with the user can choose between (triennale | magistrale)

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "regolamentodidattico")
    locale: str = update.message.from_user.language_code
    update.message.reply_text(get_locale(locale, TEXT_IDS.REG_CDL_GRAD_SELECT_TEXT_ID), reply_markup=get_cdl_keyboard(locale))


def regolamentodidattico_handler(update: Update, context: CallbackContext) -> None:
    """Called by any of the /regolamentodidattico buttons.
    Data can be ( home | triennale | magistrale ).
    Allows the used to navigate between the rulebooks

    Args:
        update: update event
        context: context passed by the handler
    """
    query: Optional[CallbackQuery] = update.callback_query
    data: str = query.data.replace("reg_button_", "")
    locale: str = update.callback_query.from_user.language_code
    if data == "home":
        context.bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=get_locale(locale, TEXT_IDS.REG_CDL_GRAD_SELECT_TEXT_ID),
                                      reply_markup=get_cdl_keyboard(locale))
    elif data == "help":
        help_cmd(query, context, True)

    else:
        context.bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=get_locale(locale, TEXT_IDS.REG_CDL_YEAR_SELECT_TEXT_ID),
                                      reply_markup=get_cdl_keyboard(locale, reg_doc=REGOLAMENTI[data]))


def cdl_handler(update: Update, context: CallbackContext) -> None:
    query: Optional[CallbackQuery] = update.callback_query
    data: str = query.data.replace("cdl_button_", "")
    locale: str = update.callback_query.from_user.language_code
    if data == "informatica":
        context.bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=get_locale(locale, TEXT_IDS.REG_CDL_INF_COURSE_TEXT_ID),
                                      reply_markup=get_inf_keyboard(locale))
    else:
        context.bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=get_locale(locale, TEXT_IDS.REG_CDL_MAT_COURSE_TEXT_ID),
                                      reply_markup=get_mat_keyboard(locale))


def send_regolamento(update: Update, context: CallbackContext) -> None:
    """Called by clicking on a rulebook.
    Sends said rulebook to the user.

    Args:
        update: update event
        context: context passed by the handler
    """
    query: Optional[CallbackQuery] = update.callback_query
    data: Optional[str] = query.data
    chat_id: int = update.effective_chat.id
    locale: str = update.callback_query.from_user.language_code
    if data in reg_doc_triennale_L31:
        doc = reg_doc_triennale_L31[data]
    elif data in reg_doc_triennale_L35:
        doc = reg_doc_triennale_L35[data]
    elif data in reg_doc_magistrale_LM18:
        doc = reg_doc_magistrale_LM18[data]
    else:
        doc = reg_doc_magistrale_LM40[data]

    context.bot.send_document(chat_id=chat_id, document=doc)
    context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=get_locale(locale, TEXT_IDS.REG_CDL_RET_FILE_TEXT_ID), )


def get_inf_keyboard(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACHELOR_TEXT_ID), callback_data='reg_button_triennale_L31'),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.MASTER_TEXT_ID), callback_data='reg_button_magistrale_LM18')],
        [InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_TO_MAIN_MENU_KEYBOARD_TEXT_ID), callback_data='reg_button_help')],
        [InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_BUTTON_TEXT_TEXT_ID), callback_data='reg_button_home')]
    ])


def get_mat_keyboard(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACHELOR_TEXT_ID), callback_data='reg_button_triennale_L35'),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.MASTER_TEXT_ID), callback_data='reg_button_magistrale_LM40')],
        [InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_TO_MAIN_MENU_KEYBOARD_TEXT_ID), callback_data='reg_button_help')],
        [InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_BUTTON_TEXT_TEXT_ID), callback_data='reg_button_home')]
    ])


def get_cdl_keyboard(locale: str, reg_doc: dict = None) -> InlineKeyboardMarkup:
    """Called by :meth:`regolamentodidattico` and :meth:`regolamentodidattico_handler`.
    Generates the whole list of rulebooks to append as an InlineKeyboard

    Args:
        locale: the user language
        reg_doc: rulebooks to show

    Returns:
        list of rulebooks
    """

    if reg_doc is None:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton('Informatica', callback_data='cdl_button_informatica'),
            InlineKeyboardButton('Matematica', callback_data='cdl_button_matematica')],
            [InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_BUTTON_TEXT_TEXT_ID), callback_data='reg_button_help')]
        ])
    keyboard = [[InlineKeyboardButton(r.split('_')[0], callback_data=r)] for r in reg_doc]
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_TO_MAIN_MENU_KEYBOARD_TEXT_ID), callback_data='reg_button_help')])  # return button
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_BUTTON_TEXT_TEXT_ID), callback_data='reg_button_home')])
    return InlineKeyboardMarkup(keyboard)
