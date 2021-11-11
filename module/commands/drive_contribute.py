import yaml
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from telegram import Update
from telegram.ext import CallbackContext

from module.utils.drive_contribute_utils import delete_drive_permission_job

with open('config/settings.yaml', 'r') as yaml_config:
    config_map = yaml.load(yaml_config, Loader=yaml.SafeLoader)


def drive_contribute(update: Update, context: CallbackContext):
    args = context.args
    chat_id = update.message.chat_id
    first_name = update.message.from_user.first_name
    username = update.message.from_user.username
    if username:
        username = f"@{username}"
    else:
        username = "Nessuno username"

    if len(args) < 2:
        context.bot.sendMessage(
            chat_id=chat_id,
            text="USO: /drive_contribute [e-mail] [motivazione]\n\nESEMPIO: /drive_contribute mario.rossi@gmail.com Vorrei caricare i miei appunti di Fondamenti di Informatica",
        )
        return

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
