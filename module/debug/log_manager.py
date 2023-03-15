"""Handles the logging of events"""
import logging
import traceback
import html
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from module.shared import config_map

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Logger enabled")


def error_handler(update: Update, context: CallbackContext):  # pylint: disable=unused-argument
    """Logs the error and notifies the admins.
    Args:
        update: update event
        context: context passed by the handler
    """
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    traceback_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    traceback_str = ''.join(traceback_list)

    min_traceback_list = [line for line in traceback_list if "module" in line and "venv" not in line]
    min_traceback_list.append(traceback_list[-1])
    min_traceback_str = ''.join(min_traceback_list)
    notify_error_admin(context=context, traceback_str=min_traceback_str)

    try:  # log the error
        message = "\n___ERROR LOG___\n"\
                        f"time: {datetime.now()}\n"\
                        f"error: {context.error}\n"\
                        f"error_traceback: {traceback_str}\n"
        if update and update.message:  # if the update contains a message, show additional info
            chat = update.message.chat
            message += f"id_message:  {update.message.message_id}\n"\
                        f"chat_id:  {chat.id}\n"\
                        f"chat_type:  {chat.type}\n"\
                        f"chat_title:  {chat.title}\n"\
                        f"message_date:  {update.message.date}\n"
            message += "_____________\n"
        with open("logs/errors.log", "a", encoding="utf8") as log_file:
            log_file.write("\n" + message)
    except AttributeError as error:
        logger.warning(error)
    except FileNotFoundError as error:
        logger.error(error)


def notify_error_admin(context: CallbackContext, traceback_str: str):
    """Sends a telegram message to notify the admins.
    Args:
        context: context passed by the handler
    """
    text = f'An exception was raised:\n' f'<pre>{html.escape(traceback_str)}</pre>'
    context.bot.send_message(chat_id=config_map['dev_group_chatid_logs'], text=text, parse_mode=ParseMode.HTML)


def log_error(header: str, error: Exception):  # pylint: disable=unused-argument
    """Logs an error
    Args:
        header: message to put before the error
        error: the error that has occurred
    """
    logger.error("%s: %s", header, error)
    try:
        message = "\n___ERROR LOG___\n"\
                    f"Log time:\n {datetime.now()}"\
                    f"Error:\n {header}: {error}"\
                    "\n------------\n"
        with open("logs/errors.log", "a", encoding="utf8") as log_file:
            log_file.write(message)
    except FileNotFoundError as e:
        logger.error(e)


def log_message(update: Update, context: CallbackContext):  # pylint: disable=unused-argument
    """Logs the message that caused the update
    Args:
        update: update event
        context: context passed by the handler
    """
    if update.message:
        try:
            user = update.message.from_user
            chat = update.message.chat
            message = f"\n___ID MESSAGE:  {update.message.message_id} ____\n"\
                        "___INFO USER___\n"\
                        f"user_id:  {user.id}\n"\
                        f"user_name:  {user.username}\n"\
                        f"user_first_lastname: {user.first_name} {user.last_name}\n"\
                        "___INFO CHAT___\n"\
                        f"chat_id:  {chat.id}\n"\
                        f"chat_type:  {chat.type}\n"\
                        f"chat_title:  {chat.title}\n"\
                        "___TESTO___\n"\
                        f"text:  {update.message.text}\n"\
                        f"date:  {update.message.date}"\
                        "\n_____________\n"
            with open("logs/messages.log", "a", encoding="utf8") as log_file:
                log_file.write("\n" + message)
        except AttributeError as error:
            logger.warning(error)
        except FileNotFoundError as error:
            logger.error(error)
