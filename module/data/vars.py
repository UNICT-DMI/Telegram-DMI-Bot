from enum import Enum, auto


# Translation IDs
class TEXT_IDS(Enum):
    # Shared misc
    SHOW_RELATED_COMMANDS_TEXT_ID = auto()
    CLOSE_KEYBOARD_TEXT_ID = auto()
    BACK_TO_MENU_KEYBOARD_TEXT_ID = auto()
    BACK_TO_MAIN_MENU_KEYBOARD_TEXT_ID = auto()
    BACK_BUTTON_TEXT_TEXT_ID = auto()
    BACHELOR_TEXT_ID = auto()
    MASTER_TEXT_ID = auto()
    FOUND_RESULT_TEXT_ID = auto()
    NO_RESULT_FOUND_TEXT_ID = auto()
    SEARCH_YEAR_TEXT_ID = auto()
    SEARCH_DAY_TEXT_ID = auto()
    SEARCH_SESSION_TEXT_ID = auto()
    SEARCH_COURSE_TEXT_ID = auto()
    SEARCH_HEADER_TEXT_ID = auto()
    SEARCH_BUTTON_TEXT_ID = auto()
    USE_WARNING_TEXT_ID = auto()
    GROUP_WARNING_TEXT_ID = auto()
    SELECT_YEAR_TEXT_ID = auto()
    YEAR_1ST_TEXT_ID = auto()
    YEAR_2ND_TEXT_ID = auto()
    YEAR_3RD_TEXT_ID = auto()
    # /start
    START_TEXT_ID = auto()
    # sticky keyboard
    HELP_KEYBOARD_TEXT_ID = auto()
    AULARIO_KEYBOARD_TEXT_ID = auto()
    CLOUD_KEYBOARD_TEXT_ID = auto()
    REPORT_TO_KEYBOARD_TEXT_ID = auto()
    # /help
    HELP_HEADER_TEXT_ID = auto()
    HELP_DIPARTIMENTO_CDL_KEYBOARD_TEXT_ID = auto()
    HELP_REGOLAMENTO_DIDATTICO_KEYBOARD_TEXT_ID = auto()
    HELP_SEGRETERIA_CONTATTI_KEYBOARD_TEXT_ID = auto()
    HELP_ERSU_ORARI_KEYBOARD_TEXT_ID = auto()
    HELP_APPUNTI_CLOUD_KEYBOARD_TEXT_ID = auto()
    HELP_PROGETTI_RICONOSCIMENTI_KEYBOARD_TEXT_ID = auto()
    HELP_ALL_COMMANDS_KEYBOARD_TEXT_ID = auto()
    HELP_ALL_COMMANDS_TOOLTIP_ID = auto()
    # /help-CDL command
    HELP_CDL_EXAMS_TEXT_ID = auto()
    HELP_CDL_LESSONS_TIMETABLE_TEXT_ID = auto()
    HELP_CDL_PROF_INFO_TEXT_ID = auto()
    HELP_CDL_REPRS_TEXT_ID = auto()
    HELP_CDL_LIBRARY_TEXT_ID = auto()
    HELP_CDL_GROUPS_TEXT_ID = auto()
    HELP_CDL_PROF_TOOLTIP_ID = auto()
    # /help-Reprs command
    REPRS_HEADER_TEXT_ID = auto()
    REPRS_DMI_TEXT_ID = auto()
    REPRS_DMI_CS_TEXT_ID = auto()
    REPRS_DMI_MATH_TEXT_ID = auto()
    # /help-Segr command
    SEGR_DID_TEXT_ID = auto()
    SEGR_STU_TEXT_ID = auto()
    SEGR_CEA_TEXT_ID = auto()
    # /help-ERSU command
    ERSU_TEXT_ID = auto()
    ERSU_OFFICE_TEXT_ID = auto()
    ERSU_URP_TEXT_ID = auto()
    # /help-projct/credits command
    PRJ_OPIS_TEXT_ID = auto()
    CREDITS_CONTRIBUTORS_TEXT_ID = auto()
    # /miscs
    MISC_GDRIVE_TEXT_ID = auto()
    MISC_GITLAB_TEXT_ID = auto()
    MISC_GDRIVE_TOOLTIP_ID = auto()
    MISC_GITLAB_TOOLTIP_ID = auto()
    # /aulario
    AULARIO_DAY_SELECTION_TEXT_ID = auto()
    AULARIO_WARNING_TEXT_ID = auto()
    AULARIO_LESSON_SELECTION_TEXT_ID = auto()
    AULARIO_NO_LESSON_WARNING_TEXT_ID = auto()
    AULARIO_LESSON_AT_TIME_TEXT_ID = auto()
    # /drive
    DRIVE_NO_USERNAME_WARNING_TEXT_ID = auto()
    DRIVE_USE_TEXT_TEXT_ID = auto()
    DRIVE_CONFIRM_ACCESS_TEXT_ID = auto()
    DRIVE_VALIDATION_ERROR_TEXT_ID = auto()
    DRIVE_HEADER_TEXT_ID = auto()
    DRIVE_ERROR_DEVS_TEXT_ID = auto()
    DRIVE_ERROR_GFILE_TEXT_ID = auto()
    DRIVE_ERROR_TOO_BIG_TEXT_ID = auto()
    # /report
    REPORT_ON_GROUP_WARNING_TEXT_ID = auto()
    REPORT_NO_USERNAME_WARNING_TEXT_ID = auto()
    REPORT_WARNING_TEXT_ID = auto()
    REPORT_RESPONSE_TEXT_ID = auto()
    # /regolamentodidattico
    REG_CDL_GRAD_SELECT_TEXT_ID = auto()
    REG_CDL_YEAR_SELECT_TEXT_ID = auto()
    REG_CDL_INF_COURSE_TEXT_ID = auto()
    REG_CDL_MAT_COURSE_TEXT_ID = auto()
    REG_CDL_RET_FILE_TEXT_ID = auto()
    # /prof
    PROF_USE_TEXT_ID = auto()
    # /lezioni
    CLASSES_SELECT_DAY_TEXT_ID = auto()
    CLASSES_SELECT_DAY1_TEXT_ID = auto()
    CLASSES_SELECT_DAY2_TEXT_ID = auto()
    CLASSES_SELECT_DAY3_TEXT_ID = auto()
    CLASSES_SELECT_DAY4_TEXT_ID = auto()
    CLASSES_SELECT_DAY5_TEXT_ID = auto()
    CLASSES_USAGE_TEXT_ID = auto()
    # /esami
    EXAMS_SELECT_SESSION_TEXT_ID = auto()
    EXAMS_SESSION_1_TEXT_ID = auto()
    EXAMS_SESSION_2_TEXT_ID = auto()
    EXAMS_SESSION_3_TEXT_ID = auto()
    EXAMS_SESSION_4_TEXT_ID = auto()
    EXAMS_USAGE_TEXT_ID = auto()


PLACE_HOLDER: str = "%capybara%"

""" stats.py """

EASTER_EGG = ("leiCheNePensaSignorina", "smonta_portoni", "santino", "bladrim", "prof_sticker", "universita_bandita")
