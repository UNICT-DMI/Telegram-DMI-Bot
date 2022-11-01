"""Constants and common functions"""
import json
import logging
from datetime import date, datetime
import yaml
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from module.data import DbManager

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# config
with open('config/settings.yaml', 'r', encoding='utf-8') as yaml_config:
    config_map = yaml.load(yaml_config, Loader=yaml.SafeLoader)

# Icons
CUSicon = {
    0: "🏋",
    1: "⚽️",
    2: "🏀",
    3: "🏈",
    4: "🏐",
    5: "🏊",
}


def send_message(update: Update, context: CallbackContext, messaggio: str):
    """Replies with a message, making sure the maximum lenght text allowed is respected

    Args:
        update: update event
        context: context passed by the handler
        messaggio: message to send
    """
    #prova a prendere il chat_id da update.message, altrimenti prova da update.callback_query.message
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
    msg = ""
    righe = messaggio.split('\n')
    for riga in righe:
        if riga.strip() == "" and len(msg) > 3000:
            try:
                context.bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='Markdown')
                msg = ""
            except BadRequest:
                logger.error("send_message: the message is badly formatted")
        else:
            msg += riga + "\n"
    context.bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='Markdown')


def read_md(namefile: str) -> str:
    """Reads a markdown file

    Args:
        namefile: name of the markdown file, without extension

    Returns:
        content of the markdown file
    """
    with open(f"data/markdown/{namefile}.md", "r", encoding="utf8") as in_file:
        text = in_file.read()
    return text


def read_json(namefile: str) -> dict:
    """Reads a json file

    Args:
        namefile: name of the json file, without extension

    Returns:
        content of the json file, as a dictionary
    """
    with open(f"data/json/{namefile}.json", "r", encoding="utf8") as in_file:
        result = json.load(in_file)
    return result


def check_log(update: Update, command_name: str, is_query: bool = False):
    """If enabled, logs the command

    Args:
        update: update event
        command_name: name of the event to log
        is_query: whether the event to log is a query. Defaults to False.
    """
    chat_id = update.callback_query.message.chat_id if is_query else update.message.chat_id

    if config_map['debug']['disable_db'] == 0:
        DbManager.insert_into(table_name="stat_list", values=(command_name, chat_id, date.today()))

def get_year_code(month: int, day: int) -> str:
    """Generates the code of the year

    Args:
        month: month
        day: day

    Returns:
        last two digits of the current year
    """
    date_time = datetime.now().astimezone()
    check_new_year = datetime(year=date_time.year, month=month, day=day).astimezone()
    year = date_time.year
    if date_time > check_new_year:
        year = date_time.year + 1
    return str(year)[-2:]


def check_print_old_exams(year_exam: str) -> bool:
    """Checks if the old exams should be considered

    Args:
        year_exam: target year

    Returns:
        whether the old exams should be considered
    """
    date_time = datetime.now().astimezone()
    ckdate = datetime(year=date_time.year, month=12, day=23).astimezone()  # aaaa/12/24 data dal quale vengono prelevati solo gli esami del nuovo anno

    return year_exam != str(date_time.year)[-2:] and date_time < ckdate
