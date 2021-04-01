"""/drive command"""
import os
from pydrive.auth import AuthError, GoogleAuth
from pydrive.drive import GoogleDrive
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from module.shared import check_log
from module.debug import log_error


def drive(update: Update, context: CallbackContext):
    """Called by the /drive command.
    Lets the user navigate the drive folders, if he has the permissions

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "drive")
    chat_id = update.message.chat_id

    gauth = GoogleAuth(settings_file="config/settings.yaml")
    gauth.CommandLineAuth()
    gdrive = GoogleDrive(gauth)

    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text="La funzione /drive non è ammessa nei gruppi")
        return

    try:
        file_list = gdrive.ListFile({'q': "'0B7-Gi4nb88hremEzWnh3QmN3ZlU' in parents and trashed=false", 'orderBy': 'folder,title'}).GetList()
    except AuthError as e:
        log_error(header="drive", error=e)

    keyboard = get_files_keyboard(file_list, row_len=3)  # keyboard that allows the user to navigate the folder
    context.bot.sendMessage(chat_id=chat_id, text="DMI UNICT - Appunti & Risorse:", reply_markup=InlineKeyboardMarkup(keyboard))


def drive_handler(update: Update, context: CallbackContext):
    """Called by any of the buttons of the /drive command.
    Allows the user to navigate in the google drive and download files

    Args:
        update: update event
        context: context passed by the handler
    """
    query_data = update.callback_query.data.replace("drive_file_", "")
    chat_id = update.callback_query.from_user.id
    bot = context.bot

    gauth = GoogleAuth(settings_file="config/settings.yaml")
    gauth.CommandLineAuth()
    gdrive = GoogleDrive(gauth)

    file1 = gdrive.CreateFile({'id': query_data})
    file1.FetchMetadata()
    if file1['mimeType'] == "application/vnd.google-apps.folder":  # the user clicked on a folder
        try:
            istance_file = gdrive.ListFile({'q': "'" + file1['id'] + "' in parents and trashed=false", 'orderBy': 'folder,title'})
            file_list = istance_file.GetList()
        except Exception as e:
            log_error(header="drive_handler", error=e)
            bot.sendMessage(chat_id=chat_id, text="Si è verificato un errore, ci scusiamo per il disagio. Contatta i devs. /help")
            return

        keyboard = get_files_keyboard(file_list)  # keyboard that allows the user to navigate the folder

        if len(file1['parents']) > 0 and file1['parents'][0]['id'] != '0ADXK_Yx5406vUk9PVA':
            keyboard.append([InlineKeyboardButton("🔙", callback_data="drive_file_" + file1['parents'][0]['id'])])

        bot.sendMessage(chat_id=chat_id, text=file1['title'] + ":", reply_markup=InlineKeyboardMarkup(keyboard))

    elif file1['mimeType'] == "application/vnd.google-apps.document":  # the user clicked on a google docs
        bot.sendMessage(chat_id=chat_id, text="Impossibile scaricare questo file poichè esso è un google document, Andare sul seguente link")
        bot.sendMessage(chat_id=chat_id, text=file1['exportLinks']['application/pdf'])

    else:  # the user clicked on a file
        try:
            file_d = gdrive.CreateFile({'id': file1['id']})
            file_d.FetchMetadata()
            if int(file_d['fileSize']) < 5e+7:
                file_path = f"file/{file1['title']}"
                file_d.GetContentFile(file_path)
                with open(file_path, "rb") as f:
                    bot.sendChatAction(chat_id=chat_id, action="UPLOAD_DOCUMENT")
                    bot.sendDocument(chat_id=chat_id, document=f)
                os.remove(file_path)
            else:
                bot.sendMessage(chat_id=chat_id, text="File troppo grande per il download diretto, scarica dal seguente link")
                bot.sendMessage(chat_id=chat_id, text=file_d['alternateLink'])
        except Exception as e:
            log_error(header="drive_handler", error=e)
    update.callback_query.answer()  # stops the spinning


def get_files_keyboard(file_list: list, row_len: int = 2) -> list:
    """Called by :meth:`drive` and :meth:`drive_handler`.
    Generates the InlineKeyboard that allows the user to navigate among the files in the list

    Args:
        file_list: list of files
        row_len: lenght of the row. Defaults to 2

    Returns:
        InlineKeyboard
    """
    formats = {
        **{
            "pdf": "📕 "
        },
        **dict.fromkeys([' a', 'b', 'c'], 10),
        **dict.fromkeys(["doc", "docx", "txt"], "📘 "),
        **dict.fromkeys(["jpg", "png", "gif"], "📷 "),
        **dict.fromkeys(["rar", "zip"], "🗄 "),
        **dict.fromkeys(["out", "exe"], "⚙ "),
        **dict.fromkeys(["c", "cpp", "h", "py", "java", "js", "html", "php"], "💻 ")
    }
    keyboard = []
    for i, file2 in enumerate(file_list):
        file2.FetchMetadata()
        if file2['mimeType'] == "application/vnd.google-apps.folder":
            icona = "🗂 "
        else:
            file_format = file2['title'][-5:]  # get last 5 characters of strings
            file_format = file_format.split(".")  # split file_format per "."
            file_format = file_format[-1]  # get last element of file_format
            icona = formats.get(file_format, "📄 ")

        if i % row_len == 0:  # the current element has an even index
            keyboard.append([InlineKeyboardButton(icona + file2['title'], callback_data="drive_file_" + file2['id'])])
        else:  # the current element has an odd index
            keyboard[i // row_len].append(InlineKeyboardButton(icona + file2['title'], callback_data="drive_file_" + file2['id']))
    return keyboard
