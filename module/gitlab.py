# -*- coding: utf-8 -*-

# Telegram
from telegram.ext import run_async, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

#Modules
from module.shared import config_map, check_log

# System libraries
from urllib.parse import quote
import requests
import sqlite3
import logging
import base64
import gitlab
import time
import re
import os

# Logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

GITLAB_AUTH_TOKEN = config_map['gitlab']['token']
GITLAB_ROOT_GROUP = config_map['gitlab']['root']

session = None
api = None
db = None

# Formats
formats = {
    **dict.fromkeys(["pdf", "epub"], "📕"),
    **dict.fromkeys(["doc", "docx", "txt"], "📘"),
    **dict.fromkeys(["jpg", "jpeg", "bmp", "png", "gif"], "📷"),
    **dict.fromkeys(["rar", "zip"], "🗄"),
    **dict.fromkeys(["out", "exe"], "⚙"),
    **dict.fromkeys(["c", "cc", "cpp", "h", "py", "java", "js", "html", "php"], "💻")
}


def git(update: Update, context: CallbackContext):
    check_log(update, "gitlab")

    chat_id = update.message.chat_id
    executed_command = update.message.text.split(' ')[0]

    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text="❗️ La funzione %s non è ammessa nei gruppi" % executed_command)
    else:
        gitlab_handler(update, context)


def new_session(token):
    """
        Create a new session using the authentication token passed as argument.

        Parameters:
            token: Authentication Token for GitLab APIs
    """

    global session

    session = requests.Session()
    session.headers.update({'Private-Token': token})


def init_api():
    """ Initialize the GitLab APIs """

    global api
    global session

    if not api:
        logger.info(msg="API Initialized")

        new_session(GITLAB_AUTH_TOKEN)
        api = gitlab.Gitlab(url='https://gitlab.com', api_version=4, session=session)


def get_chat_id(update: Update):
    """
        Return the chat ID from update object

        Parameters:
            update: "update" object of Telegram API
    """

    chat_id = None

    if hasattr(update, "callback_query") and hasattr(update.callback_query, "message"):
        chat_id = update.callback_query.message.chat.id

    if not chat_id:
        chat_id = update.message.chat_id

    return chat_id


def get_subgroups(group_id):
    """
        Returns an array containing subgroups of a group

        Paramaters:
            group_id: Parent group ID
    """

    global api

    try:
        return api.groups.get(group_id).subgroups.list()
    except gitlab.GitlabGetError:
        return []


def get_projects(group_id):
    """
        Returns an array containing projects of a group

        Paramaters:
            group_id: Parent group ID
    """

    global api

    try:
        return api.groups.get(group_id).projects.list()
    except gitlab.GitlabGetError:
        return []


def get_repository_tree(project_id, path='/', recursive=False):
    """
        Return the repository tree

        Parameters:
            project_id: Project ID
            path: Folder path of the project (default: '/')
            recursive: If True return every file or directory of the repository (default: False)
    """

    global api

    try:
        return api.projects.get(project_id).repository_tree(path=path, recursive=recursive)
    except gitlab.GitlabGetError:
        return None


def explore_repository_tree(origin_id, path='/', db=None):
    """
        Explore a repository analyzing for files and directories

        Parameters:
            origin_id: Origin repository ID
            path: (default: '/')
            db: (default: None)
    """

    buttons = []
    repository_tree = get_repository_tree(origin_id, path)

    for item in repository_tree:
        if item['name'].startswith('.'):
            continue

        if db:
            db.execute("INSERT OR REPLACE INTO gitlab (id, parent_id, name, pathname, type) VALUES (?, ?, ?, ?, ?)",
                       (item['id'], origin_id, item['name'], item['path'], item['type']))

        if item['type'] == 'blob':
            item_extension = os.path.splitext(item['name'])[1].replace('.', '')
            format_icon = formats.get(item_extension, "📄")

            buttons.append(InlineKeyboardButton("%s %s" % (format_icon, item['name']), callback_data='git_b_%s_%s' % (origin_id, item['id'])))
        elif item['type'] == 'tree':
            buttons.append(InlineKeyboardButton("🗂 %s" % item['name'], callback_data='git_t_%s_%s' % (origin_id, item['id'])))

    return buttons


def get_blob_file(project_id, blob_id):
    """
        Return blob object

        Parameters:
            project_id: Project ID
            blob_id: Blob ID
    """

    global api

    try:
        blob_file = api.projects.get(project_id).repository_blob(blob_id)

        if type(blob_file['content']) == str:
            blob_content = blob_file['content']
        else:
            blob_content = base64.b64decode(blob_file['content']).decode()
        blob_size = blob_file['size']

        if blob_content.startswith('version https://git-lfs.github.com/spec/v1'):
            blob_size = re.findall('size (\d+)?', blob_content)[0]

        return {'size': blob_size, 'content': blob_content}
    except gitlab.GitlabGetError:
        print('Problem during the download of file from gitlab')


@run_async
def download_blob_file_async_internal(update: Update, context: CallbackContext, blob_id, blob_name, db_result):
    """
        Download a file asynchronously and send it if the size is less than 50MB, otherwise send the download link

        Parameters:
            bot: "bot" object of Telegram API
            update: "update" object of Telegram API
            blob_id: The id of file to download
            blob_name: The name of file to download
            db_result: The result of query to achieve web_url, pathname and parent_id
    """

    global session

    chat_id = get_chat_id(update)

    if chat_id:
        web_url, pathname, parent_id = db_result
        blob_info = get_blob_file(parent_id, blob_id)
        download_url = "%s/raw/master/%s" % (web_url, quote(pathname))

        if int(blob_info['size']) < 4.5e+7:
            file_name = "%s_%s" % (time.time(), blob_name)

            with open('file/%s' % file_name, 'wb') as file_handle:
                with session.get(download_url, stream=True) as download:
                    file_handle.write(download.content)

            with open('file/%s' % file_name, 'rb') as downloaded_file:
                context.bot.sendChatAction(chat_id=chat_id, action="UPLOAD_DOCUMENT")
                context.bot.sendDocument(chat_id=chat_id, document=downloaded_file)

            os.remove('file/%s' % file_name)
        else:
            context.bot.sendMessage(chat_id=chat_id,
                                    text="⚠️ Il file è troppo grande per il download diretto!\nScaricalo al seguente link:\n%s" % download_url)


def download_blob_file_async(update: Update, context: CallbackContext, blob=None):
    """
        Return the handle to the file if below the maximum size otherwise the download link

        Parameters:
            bot: "bot" object of Telegram API
            update: "update" object of Telegram API
            blob: Object containing ID and name of a blob (default: None)
    """

    global db
    global api
    global session

    if blob:
        blob_id, blob_name = blob['id'], blob['name']

        query = "SELECT * FROM\
            (SELECT web_url FROM gitlab WHERE id = (\
                SELECT parent_id FROM gitlab WHERE id = '{0}'\
            )),\
            (SELECT pathname FROM gitlab WHERE id = '{0}'),\
            (SELECT parent_id FROM gitlab WHERE id = '{0}')"

        db_result = db.execute(query.format(blob_id)).fetchone()
        download_blob_file_async_internal(update, context, blob_id, blob_name, db_result)


def format_keyboard_buttons(buttons=[]):
    """
        Place the buttons on multiple lines if possible

        Parameters:
            buttons: Array containing the buttons to display (default: [])
    """

    keyboard = [[]]
    number_row = 0
    number_array = 0

    for button in buttons:
        if isinstance(button, InlineKeyboardButton):
            if number_row >= 1:
                keyboard.append([button])
                number_array += 1
                number_row = 0
            else:
                keyboard[number_array].append(button)
                number_row += 1
        else:
            keyboard.append([button[0]])

    return keyboard


def send_message(update: Update, context: CallbackContext, message, buttons=[[]], blob=None):
    """
        Send a reply message with text and button or upload a document

        Parameters:
            bot: "bot" object of Telegram API
            update: "update" object of Telegram API
            message: Message text
            buttons: Array of answer buttons (default: [[]])
            blob: Object that specifies the blob file to download (default: None)
    """

    chat_id = get_chat_id(update)

    if chat_id:
        if blob:
            download_blob_file_async(update, context, blob)
        else:
            buttons = format_keyboard_buttons(buttons)
            reply_markup = InlineKeyboardMarkup(buttons)

            context.bot.sendMessage(chat_id=chat_id, text=message, reply_markup=reply_markup)


def gitlab_handler(update: Update, context: CallbackContext):
    """
        Handle every action of /git and /gitlab command

        Parameters:
            bot: "bot" object of Telegram API
            update: "update" object of Telegram API
    """

    global db

    init_api()
    db = sqlite3.connect('data/DMI_DB.db')

    blob = None
    blob_id = None
    origin_id = None

    parent = (GITLAB_ROOT_GROUP, "DMI UNICT - Appunti & Risorse:")
    buttons = []

    data = None
    query = update.callback_query
    if query is not None and query.data is not None:
        data = query.data.replace("git_", "")

    if not data:
        subgroups = get_subgroups(GITLAB_ROOT_GROUP)

        for subgroup in subgroups:
            db.execute("INSERT OR REPLACE INTO gitlab (id, parent_id, name, type) VALUES (?, ?, ?, ?)",
                       (subgroup.id, subgroup.parent_id, subgroup.name, 'subgroup'))
            buttons.append(InlineKeyboardButton("🗂 %s" % subgroup.name, callback_data='git_s_%s' % subgroup.id))
    else:
        action, origin_id, blob_id = (data.split('_') + [None] * 3)[:3]

        if blob_id:
            query = "SELECT * FROM\
                (SELECT parent_id, name FROM gitlab WHERE id = %s),\
                (SELECT name FROM gitlab WHERE id = '%s')"

            db_result = db.execute(query % (origin_id, blob_id)).fetchone()
        else:
            db_result = db.execute("SELECT parent_id, name FROM gitlab WHERE id = %s" % origin_id).fetchone()

        if db_result:
            parent = db_result

        if action == 'x':
            _type = db.execute('SELECT type FROM gitlab WHERE id = %s' % origin_id).fetchone()
            action = (_type[0] if _type else 'subgroup')[0]

        if action == 's':
            subgroups = get_subgroups(origin_id)

            if subgroups:
                for subgroup in subgroups:
                    db.execute("INSERT OR REPLACE INTO gitlab (id, parent_id, name, type) VALUES (?, ?, ?, ?)",
                               (subgroup.id, subgroup.parent_id, subgroup.name, 'subgroup'))
                    buttons.append(InlineKeyboardButton("🗂 %s" % subgroup.name, callback_data='git_s_%s' % subgroup.id))

            projects = get_projects(origin_id)

            for project in projects:
                db.execute("INSERT OR REPLACE INTO gitlab (id, parent_id, name, web_url, type) VALUES (?, ?, ?, ?, ?)",
                           (project.id, origin_id, project.name, project.web_url, 'project'))
                buttons.append(InlineKeyboardButton("🗂 %s" % project.name, callback_data='git_p_%s' % project.id))
        elif action == 'p':
            buttons.extend(explore_repository_tree(origin_id, '/', db))
        elif action == 't':
            path = db.execute("SELECT pathname FROM gitlab WHERE id = '%s'" % blob_id).fetchone()
            buttons.extend(explore_repository_tree(origin_id, path, db))
        elif action == 'b':
            blob = {'id': blob_id, 'name': parent[2]}

        if origin_id != str(GITLAB_ROOT_GROUP):
            buttons.append([InlineKeyboardButton("🔙", callback_data='git_x_%s' % parent[0])])

    title = parent[2] if blob_id and len(parent) == 3 else parent[1]
    send_message(update, context, title, buttons, blob)

    db.commit()
    db.close()
