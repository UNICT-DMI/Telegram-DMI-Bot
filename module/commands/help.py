"""/help command"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from module.shared import check_log
from module.data.vars import TEXT_IDS
from module.utils.multi_lang_utils import get_locale, get_locale_code


def help_cmd(update: Update, context: CallbackContext, edit: bool = False) -> None:
    """Called by the /help command.
    Shows all the actions supported by the bot

    Args:
        update: update event
        context: context passed by the handler
        edit: bool flag that affects how the message should be handled
    """
    check_log(update, "help")
    chat_id: int = update.message.chat_id
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.HELP_HEADER_TEXT_ID)

    keyboard = [[]]
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_DIPARTIMENTO_CDL_KEYBOARD_TEXT_ID),
                                          callback_data="sm_help_dip_cdl")])
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_APPUNTI_CLOUD_KEYBOARD_TEXT_ID),
                                          callback_data="sm_help_misc")])
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_SEGRETERIA_CONTATTI_KEYBOARD_TEXT_ID),
                                          callback_data="sm_help_segr")])
    keyboard.append(
        [InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_ERSU_ORARI_KEYBOARD_TEXT_ID), callback_data="sm_help_ersu")])
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_REGOLAMENTO_DIDATTICO_KEYBOARD_TEXT_ID),
                                          callback_data="reg_button_home")])
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_PROGETTI_RICONOSCIMENTI_KEYBOARD_TEXT_ID),
                                          callback_data="sm_help_projects_acknowledgements")])
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.MERCATINO_LIBRI_KEYBOARD_TEXT_ID), callback_data="md_mercatino")])
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_FAQ_TOOLTIP_ID), callback_data="md_faq")])
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_ALL_COMMANDS_KEYBOARD_TEXT_ID), callback_data="localization_HELP_ALL_COMMANDS_TOOLTIP_ID"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.CLOSE_KEYBOARD_TEXT_ID), callback_data="exit_cmd")
    ])

    reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(keyboard)
    if edit:
        context.bot.editMessageText(text=message_text, chat_id=update.message.chat_id,
                                    message_id=update.message.message_id, reply_markup=reply_markup)
    else:
        context.bot.sendMessage(chat_id=chat_id, text=message_text, reply_markup=reply_markup)


def help_back_to_menu(update: Update, context: CallbackContext) -> None:
    """Called by a sm_help_back_to_menu button from the sub menu.
    Allows the user to return back to the command list

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat the command was invoked from
        message_id: id of the help message
    """
    help_cmd(update, context, True)


def help_dip_cdl(update: Update, context: CallbackContext, chat_id: int, message_id: int) -> None:
    """Called by the sm_help_dip_cdl button from the /help command.
    Lists to the user the commands related to the department or the CDL

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat the command was invoked from
        message_id: id of the help message
    """
    # Needed due to router obfuscation
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.SHOW_RELATED_COMMANDS_TEXT_ID)

    keyboard = [[]]
    keyboard.append(
        [InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_DIPARTIMENTO_CDL_KEYBOARD_TEXT_ID), callback_data="NONE")])
    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_CDL_EXAMS_TEXT_ID), callback_data="localization_HELP_CDL_EXAMS_LINK_TOOLTIP_ID"),
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.AULARIO_KEYBOARD_TEXT_ID), callback_data="sm_aulario")
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_CDL_LESSONS_TIMETABLE_TEXT_ID),
                                 callback_data="localization_HELP_CDL_CLASSES_LINK_TOOLTIP_ID"),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_CDL_REPRS_TEXT_ID), callback_data="sm_help_rapp_menu"),

        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_CDL_LIBRARY_TEXT_ID), callback_data="localization_HELP_CDL_LIBRARY_TOOLTIP_ID"),
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_CDL_GROUPS_TEXT_ID), callback_data="md_gruppi"),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_CDL_PROF_INFO_TEXT_ID), callback_data="localization_HELP_CDL_PROF_TOOLTIP_ID"),
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID),
                                 callback_data="sm_help_back_to_menu"),
        ]
    )
    reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(keyboard)

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)


def help_rapp_menu(update: Update, context: CallbackContext, chat_id: int, message_id: int) -> None:
    """Called by the sm_help_rapp_menu button from the /help command.
    Allows the user to select the department

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat the command was invoked from
        message_id: id of the help message
    """
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.REPRS_HEADER_TEXT_ID)

    keyboard = [[]]
    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.REPRS_DMI_TEXT_ID), callback_data="localization_REPRS_DMI_TOOLTIP_ID"),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.REPRS_DMI_CS_TEXT_ID),
                                 callback_data="localization_REPRS_DMI_CS_TOOLTIP_ID"),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.REPRS_DMI_MATH_TEXT_ID),
                                 callback_data="localization_REPRS_DMI_MATH_TOOLTIP_ID"),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID),
                                 callback_data="sm_help_back_to_menu"),
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)


def help_segr(update: Update, context: CallbackContext, chat_id: int, message_id: int) -> None:
    """Called by the sm_help_segr button from the /help command.
    Lists to the user the commands related to the secretariats' office hours

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat the command was invoked from
        message_id: id of the help message
    """
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.SHOW_RELATED_COMMANDS_TEXT_ID)

    keyboard = [[]]
    keyboard.append(
        [InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_SEGRETERIA_CONTATTI_KEYBOARD_TEXT_ID), callback_data="NONE")])

    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEGR_DID_TEXT_ID), callback_data="localization_SEGR_DID_TOOLTIP_ID"),
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEGR_STU_TEXT_ID), callback_data="localization_SEGR_STU_TOOLTIP_ID"),
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEGR_CEA_TEXT_ID), callback_data="localization_SEGR_CEA_TOOLTIP_ID")
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID), callback_data="sm_help_back_to_menu"),
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)


def help_ersu(update: Update, context: CallbackContext, chat_id: int, message_id: int) -> None:
    """Called by the sm_help_ersu button from the /help command.
    Lists to the user the commands related to the ERSU

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat the command was invoked from
        message_id: id of the help message
    """
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.SHOW_RELATED_COMMANDS_TEXT_ID)

    keyboard = [[]]
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_ERSU_ORARI_KEYBOARD_TEXT_ID), callback_data="NONE")])

    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.ERSU_TEXT_ID), callback_data="localization_ERSU_TOOLTIP_ID"),
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.ERSU_OFFICE_TEXT_ID), callback_data="localization_ERSU_OFFICE_TOOLTIP_ID"),
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.ERSU_URP_TEXT_ID), callback_data="localization_ERSU_URP_TOOLTIP_ID")
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID), callback_data="sm_help_back_to_menu"),
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)


def help_projects_acknowledgements(update: Update, context: CallbackContext, chat_id: int, message_id: int) -> None:
    """Called by the sm_help_projects_acknowledgements button from the /help command.
    Lists to the user the commands related to the other's project and acknowledgements

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat the command was invoked from
        message_id: id of the help message
    """
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.SHOW_RELATED_COMMANDS_TEXT_ID)

    keyboard = [[]]
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_PROGETTI_RICONOSCIMENTI_KEYBOARD_TEXT_ID),
                                          callback_data="NONE")])

    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.PRJ_OPIS_TEXT_ID), callback_data="md_opismanager"),
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.CREDITS_CONTRIBUTORS_TEXT_ID),
                                 callback_data="md_contributors")
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID),
                                 callback_data="sm_help_back_to_menu"),
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)


def help_misc(update: Update, context: CallbackContext, chat_id: int, message_id: int) -> None:
    """Called by the sm_help_misc button from the /help command.
    Lists to the user the commands related to the miscellaneous stuff

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat the command was invoked from
        message_id: id of the help message
    """
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.SHOW_RELATED_COMMANDS_TEXT_ID)

    keyboard = [[]]
    keyboard.append(
        [InlineKeyboardButton(get_locale(locale, TEXT_IDS.HELP_APPUNTI_CLOUD_KEYBOARD_TEXT_ID), callback_data="NONE")])

    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.MISC_GDRIVE_TEXT_ID), callback_data="localization_MISC_GDRIVE_TOOLTIP_ID"),
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.MISC_GITLAB_TEXT_ID), callback_data="localization_MISC_GITLAB_TOOLTIP_ID")
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID),
                                 callback_data="sm_help_back_to_menu"),
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
