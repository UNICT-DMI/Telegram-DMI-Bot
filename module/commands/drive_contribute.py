from typing import Optional

import yaml
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import ApiRequestError
from telegram import Update
from telegram.ext import CallbackContext
from telegram.error import BadRequest

from module.utils.drive_contribute_utils import delete_drive_permission_job
from module.data.vars import TEXT_IDS
from module.utils.multi_lang_utils import get_locale

with open('config/settings.yaml', 'r', encoding='UTF-8') as yaml_config:
    config_map = yaml.load(yaml_config, Loader=yaml.SafeLoader)


def drive_contribute(update: Update, context: CallbackContext) -> None:
    args: Optional[list[str]] = context.args
    chat_id: int = update.message.chat_id
    first_name: str = update.message.from_user.first_name
    username: str = update.message.from_user.username
    locale: str = update.message.from_user.language_code
    if username:
        username = f"@{username}"
    else:
        username = get_locale(locale, TEXT_IDS.DRIVE_NO_USERNAME_WARNING_TEXT_ID)

    if len(args) < 2:
        context.bot.sendMessage(
            chat_id=chat_id,
            text=get_locale(locale, TEXT_IDS.DRIVE_USE_TEXT_TEXT_ID),
        )
        return

    try:
        email = args[0]
        reason = ' '.join(args[1:])

        request_message = context.bot.sendMessage(
            chat_id=config_map["dev_group_chatid"],
            text=f"L'utente {first_name} (Username: {username}, E-mail: {email}) ha avuto accesso in scrittura a Drive con la seguente motivazione:\n\n{reason}",
        )

        gauth = GoogleAuth(settings_file="config/settings.yaml")
        gauth.CommandLineAuth()
        gdrive = GoogleDrive(gauth)

        drive_root_folder = gdrive.CreateFile({'id': config_map['drive_folder_id']})
        drive_root_folder.FetchMetadata(fields='permissions')
        permission = drive_root_folder.InsertPermission(
            {'type': 'user', 'emailAddress': email, 'value': email, 'role': 'writer'}
        )

        context.dispatcher.job_queue.run_once(
            delete_drive_permission_job,
            when=config_map['drive_permission_duration'] * 60 * 60,
            context={
                "folder_obj": drive_root_folder,
                "permission_obj": permission,
                "request_message": request_message,
            },
        )

        context.bot.sendMessage(
            chat_id=update.message.chat_id,
            text=f'{get_locale(locale, TEXT_IDS.DRIVE_CONFIRM_ACCESS_TEXT_ID)}',
        )
    except (BadRequest, ApiRequestError):
        context.bot.sendMessage(
            chat_id=update.message.chat_id,
            text=f'{get_locale(locale, TEXT_IDS.DRIVE_VALIDATION_ERROR_TEXT_ID)}',
        )
