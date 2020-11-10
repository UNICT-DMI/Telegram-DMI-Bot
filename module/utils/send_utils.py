
# Telegram
from telegram import Update
from telegram.ext import CallbackContext

# Modules
from ..shared import config_map

def send_log(update: Update, context: CallbackContext):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        context.bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/logs.txt', 'rb'))

def send_chat_ids(update: Update, context: CallbackContext):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        context.bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/chatid.txt', 'rb'))

def send_errors(update: Update, context: CallbackContext):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        context.bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/errors.txt', 'rb'))