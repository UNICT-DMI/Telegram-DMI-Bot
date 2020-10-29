# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from module.shared import check_log

FIRST_TEXT = 'Scegliere uno dei seguenti corsi:'
IMM_TEXT = 'Scegliere il regolamento in base al proprio anno di immatricolazione:'

BACK_BUTTON = [InlineKeyboardButton('Indietro', callback_data='regdid_button')]

REGOLAMENTODIDATTICO_KEYBOARD = InlineKeyboardMarkup([
  [
    InlineKeyboardButton('Triennale', callback_data='reg_triennale_button'),
    InlineKeyboardButton('Magistrale', callback_data='reg_magistrale_button')
  ]
])

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

def regolamentodidattico(update: Update, context: CallbackContext) -> None:
  check_log(update, context, "regolamentodidattico")
  update.message.reply_text(FIRST_TEXT, reply_markup=REGOLAMENTODIDATTICO_KEYBOARD)

def regolamentodidattico_button(update: Update, context: CallbackContext) -> None:
  check_log(update, context, "regolamentodidattico", 1)

  query = update.callback_query
  context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=FIRST_TEXT, reply_markup=REGOLAMENTODIDATTICO_KEYBOARD)

def regdid(update: Update, context: CallbackContext) -> None:
  query = update.callback_query
  context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=FIRST_TEXT, reply_markup=REGOLAMENTODIDATTICO_KEYBOARD)

def triennale(update: Update, context: CallbackContext) -> None:
  query = update.callback_query
  context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=IMM_TEXT, reply_markup=get_reg_keyboard(reg_doc_triennale))

def magistrale(update: Update, context: CallbackContext) -> None:
  query = update.callback_query
  context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=IMM_TEXT, reply_markup=get_reg_keyboard(reg_doc_magistrale))

def regolamenti(update: Update, context: CallbackContext) -> None:
  query = update.callback_query
  data = query.data
  chat_id = update.effective_chat.id

  context.bot.send_document(chat_id=chat_id, document=send_reg_doc(data))
  context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text="Ecco il file richiesto:",)

def send_reg_doc(data: str) -> str:
  if data in reg_doc_triennale:
    return reg_doc_triennale[data]
  else:
    return reg_doc_magistrale[data]

def get_reg_keyboard(reg_doc: dict) -> InlineKeyboardMarkup:
  keyboard = [
    [InlineKeyboardButton(r.replace('_m', ''), callback_data=r)] for r in reg_doc
  ]
  keyboard.append(BACK_BUTTON)
  return InlineKeyboardMarkup(keyboard)
