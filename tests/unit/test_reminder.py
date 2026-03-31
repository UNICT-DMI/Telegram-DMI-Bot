# -*- coding: utf-8 -*-
"""Test suite for the /reminder command."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from module.commands.reminder import (
    TEXT_IDS,
    reminder,
    reminder_annullato_handler,
    reminder_appello_handler,
    reminder_button_appello,
    reminder_button_sessione,
    reminder_confermato_handler,
    reminder_del_button,
    reminder_del_handler,
    reminder_input_insegnamento,
    reminder_new_handler,
    reminder_prof_handler,
    reminder_send_message,
    reminder_sessione_handler,
)
from module.job_updater import check_exam_reminders

# ---- check_exam_reminders() in module/job_updater.py


@patch('module.job_updater.datetime')
@patch('module.job_updater.DbManager')
@patch('module.job_updater.reminder_send_message')
def test_check_exam_reminders_success(mock_reminder_send, mock_db, mock_datetime):
    """Verifica il calcolo date e l'invio quando ci sono risultati"""
    mock_context = MagicMock()

    fixed_now = datetime(2026, 4, 1)
    mock_datetime.now.return_value = fixed_now

    expected_14 = "2026-04-15"
    expected_4 = "2026-04-05"

    mock_db.select_from.return_value = [{'studenti': 123, 'data': expected_14}]

    check_exam_reminders(mock_context)

    mock_db.select_from.assert_called_once_with(
        table_name="exams_reg",
        where="data IN (?, ?)",
        where_args=(expected_14, expected_4),
    )

    mock_reminder_send.assert_called_once_with(
        [{'studenti': 123, 'data': expected_14}], mock_context, expected_14, expected_4
    )


@patch('module.job_updater.DbManager')
@patch('module.job_updater.reminder_send_message')
def test_check_exam_reminders_no_results(mock_reminder_send, mock_db):
    """Verifica il non invio quando non ci sono risultati"""
    mock_context = MagicMock()
    mock_db.select_from.return_value = []

    check_exam_reminders(mock_context)

    assert mock_db.select_from.called
    mock_reminder_send.assert_not_called()


# ---- reminder() in module/commands/reminder.py
@patch('module.job_updater.DbManager')
@patch('module.job_updater.logger')
def test_check_exam_reminders_db_error(mock_logger, mock_db):
    """Verifica la gestione delle eccezioni e il logging degli errori"""
    mock_context = MagicMock()

    mock_db.select_from.side_effect = Exception("Errore di connessione")

    check_exam_reminders(mock_context)

    assert mock_logger.error.called
    log_msg = mock_logger.error.call_args[0][0]
    assert "Database error" in log_msg


def test_reminder_success_private_chat():
    """Test reminder() function in a private chat."""
    mock_update = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.chat_id = 12345
    mock_update.message.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {}

    with patch("module.commands.reminder.check_log"), patch(
        "module.commands.reminder.get_locale", return_value="test"
    ):
        reminder(mock_update, mock_context)

        assert "reminder" in mock_context.user_data
        assert mock_context.bot.send_message.call_count == 1
        mock_context.bot.send_message.assert_called_with(
            chat_id=12345,
            text="test",
            reply_markup=mock_context.bot.send_message.call_args[1]["reply_markup"],
        )


def test_reminder_warning_in_group():
    """Test reminder() function warns when used in a group chat."""
    mock_update = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.chat_id = -987654
    mock_update.message.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {}

    with patch("module.commands.reminder.check_log"), patch(
        "module.commands.reminder.get_locale", return_value="Warning"
    ):
        reminder(mock_update, mock_context)

        assert mock_context.bot.sendMessage.call_count == 2
        assert mock_context.bot.send_message.call_count == 1


# ---- reminder_new_handler() in module/commands/reminder.py


def test_reminder_new_handler():
    """Test reminder_new_handler() sets the correct command state."""
    mock_update = MagicMock()
    mock_query = mock_update.callback_query
    mock_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {}}

    with patch("module.commands.reminder.get_locale", return_value="Inserisci esame"):
        reminder_new_handler(mock_update, mock_context)

        mock_query.answer.assert_called_once()
        assert mock_context.user_data["reminder"]["cmd"] == "input_insegnamento"
        mock_context.bot.send_message.assert_called_once_with(
            chat_id=mock_query.message.chat_id, text="Inserisci esame"
        )


# ---- reminder_del_button() in module/commands/reminder.py


@patch("module.commands.reminder.ExamRegistration.find_by_student")
def test_reminder_del_button(mock_find_by_student):
    """Test reminder_del_button() generates keyboard with existing reminders."""
    mock_update = MagicMock()
    mock_query = mock_update.callback_query
    mock_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {}}

    mock_exam_1 = MagicMock(insegnamento="Analisi", data="2026-06-15")
    mock_find_by_student.return_value = [mock_exam_1]

    with patch(
        "module.commands.reminder.get_locale", return_value="Seleziona da eliminare"
    ):
        reminder_del_button(mock_update, mock_context)

        assert len(mock_context.user_data["reminder"]["reminder_list"]) == 1
        mock_context.bot.send_message.assert_called_once()
        kwargs = mock_context.bot.send_message.call_args.kwargs
        assert "reply_markup" in kwargs


# ---- reminder_del_handler() in module/commands/reminder.pyy


@patch("module.commands.reminder.DbManager.delete_from")
def test_reminder_del_handler_single(mock_delete_from):
    """Test reminder_del_handler() deleting a specific reminder."""
    mock_update = MagicMock()
    mock_query = mock_update.callback_query
    mock_query.data = "rem_delete_0"
    mock_query.from_user.language_code = "it"

    mock_exam = MagicMock(
        studenti="123", insegnamento="Analisi", docenti="Rossi", data="2026-06-15"
    )
    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {"reminder_list": [mock_exam]}}

    with patch("module.commands.reminder.get_locale", return_value="Eliminato"):
        reminder_del_handler(mock_update, mock_context)

        mock_delete_from.assert_called_once_with(
            table_name="exams_reg",
            where="studenti = ? AND insegnamento = ? AND docenti = ?",
            where_args=("123", "Analisi", "Rossi"),
        )
        mock_context.bot.send_message.assert_called_once()


@patch("module.commands.reminder.DbManager.delete_from")
def test_reminder_del_handler_all(mock_delete_from):
    """Test reminder_del_handler() deleting all reminders for a user."""
    mock_update = MagicMock()
    mock_query = mock_update.callback_query
    mock_query.data = "rem_delete_-1"
    mock_query.from_user.language_code = "it"

    mock_context = MagicMock()

    with patch("module.commands.reminder.get_locale", return_value="Tutti eliminati"):
        reminder_del_handler(mock_update, mock_context)

        mock_delete_from.assert_called_once()
        mock_context.bot.send_message.assert_called_once()


@patch("module.commands.reminder.DbManager.delete_from")
def test_reminder_del_handler_db_exception(mock_delete_from):
    """Test reminder_del_handler() invia il report warning se il DB fallisce."""
    mock_update = MagicMock()
    mock_update.callback_query.data = "rem_delete_-1"
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()

    # Simuliamo un crash del DB
    mock_delete_from.side_effect = Exception("Errore fatale DB")

    with patch("module.commands.reminder.get_locale", return_value="Errore di sistema"):
        reminder_del_handler(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once_with(
            chat_id=mock_update.callback_query.message.chat_id,
            text="Errore di sistema",
            parse_mode='Markdown',
        )


# ---- reminder_button_sessione() in module/commands/reminder.py


@patch("module.commands.reminder.get_locale")
def test_reminder_button_sessione(mock_get_locale):
    """Test reminder_button_sessione() generates the correct session keyboard."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    chat_id = 12345
    message_id = 67890

    mock_get_locale.return_value = "Mocked string"

    # Call the function
    reminder_button_sessione(
        update=mock_update, context=mock_context, chat_id=chat_id, message_id=message_id
    )

    mock_context.bot.editMessageText.assert_called_once()

    call_kwargs = mock_context.bot.editMessageText.call_args.kwargs

    assert call_kwargs["chat_id"] == chat_id
    assert call_kwargs["message_id"] == message_id
    assert call_kwargs["text"] == "Mocked string"

    reply_markup = call_kwargs["reply_markup"]
    assert reply_markup is not None
    assert len(reply_markup.inline_keyboard) == 2
    assert len(reply_markup.inline_keyboard[0]) == 2
    assert len(reply_markup.inline_keyboard[1]) == 2

    assert reply_markup.inline_keyboard[0][0].callback_data == "rem_sess_prima"
    assert reply_markup.inline_keyboard[0][1].callback_data == "rem_sess_seconda"
    assert reply_markup.inline_keyboard[1][0].callback_data == "rem_sess_terza"
    assert reply_markup.inline_keyboard[1][1].callback_data == "rem_sess_straordinaria"


# ---- reminder_input_insegnamento() in module/commands/reminder.py


@patch("module.commands.reminder.Exam.find")
def test_reminder_input_insegnamento(mock_exam_find):
    """Test reminder_input_insegnamento() populates temp_exams_list properly."""
    mock_update = MagicMock()
    mock_update.message.from_user.language_code = "it"
    mock_update.message.text = "ins: Analisi"

    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {"cmd": "input_insegnamento"}}

    exam1 = MagicMock(insegnamento="Analisi 1", docenti="Prof. Rossi")
    mock_exam_find.return_value = [exam1]

    with patch("module.commands.reminder.get_locale", return_value="Seleziona prof"):
        reminder_input_insegnamento(mock_update, mock_context)

        assert "cmd" not in mock_context.user_data["reminder"]
        assert len(mock_context.user_data["reminder"]["temp_exams_list"]) == 1
        assert (
            mock_context.user_data["reminder"]["temp_exams_list"][0]["prof"]
            == "Prof. Rossi"
        )
        mock_context.bot.send_message.assert_called_once()


# ---- reminder_prof_handler() in module/commands/reminder.py


@patch("module.commands.reminder.reminder_button_sessione")
def test_reminder_prof_handler(mock_but_sess):
    """Test reminder_prof_handler() sets the professor and calls session keyboard."""
    mock_update = MagicMock()
    mock_query = mock_update.callback_query
    mock_query.data = "rem_prof_0"

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {"temp_exams_list": [{"subj": "Analisi", "prof": "Prof. Rossi"}]}
    }

    reminder_prof_handler(mock_update, mock_context)

    assert mock_context.user_data["reminder"]["professore"] == "Prof. Rossi"
    assert "temp_exams_list" not in mock_context.user_data["reminder"]
    mock_but_sess.assert_called_once()


# ---- reminder_sessione-handler() in module/commands/reminder.py


@patch("module.commands.reminder.reminder_button_appello")
def test_reminder_sessione_handler(mock_button_appello):
    """Test reminder_sessione_handler() sets session and moves to appello."""
    mock_update = MagicMock()
    mock_update.callback_query.data = "rem_sess_prima"

    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {}}

    reminder_sessione_handler(mock_update, mock_context)

    assert mock_context.user_data["reminder"]["sessione"] == "prima"
    mock_button_appello.assert_called_once()


# ---- reminder_appello_handler() in module/commands/reminder.py


def test_reminder_appello_handler():
    """Test reminder_appello_handler() asks for confirmation."""
    mock_update = MagicMock()
    mock_update.callback_query.data = "rem_appello_15-06-2026"
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {"insegnamento": "Analisi", "professore": "Rossi"}
    }

    with patch("module.commands.reminder.get_locale", return_value="Confermi?"):
        reminder_appello_handler(mock_update, mock_context)

        assert mock_context.user_data["reminder"]["appello"] == "15-06-2026"
        mock_context.bot.editMessageText.assert_called_once()


# ---- reminder_confrmato_handler() in module/commands/reminder.py


@patch("module.commands.reminder.ExamRegistration")
def test_reminder_confermato_handler(mock_exam_reg):
    """Test reminder_confermato_handler() successfully saves to DB."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {
            "appello": "15/06/2026",
            "insegnamento": "Analisi",
            "professore": "Rossi",
        }
    }

    mock_instance = mock_exam_reg.return_value

    with patch("module.commands.reminder.get_locale", return_value="Salvato"):
        reminder_confermato_handler(mock_update, mock_context)

        mock_instance.save.assert_called_once()
        assert not mock_context.user_data["reminder"]  # Should be cleared
        mock_context.bot.editMessageText.assert_called_once()


@patch("module.commands.reminder.ExamRegistration")
def test_reminder_confermato_handler_db_exception(mock_exam_reg):
    """Test reminder_confermato_handler() handles database exceptions gracefully."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {
            "appello": "15-06-2026",
            "insegnamento": "Analisi",
            "professore": "Rossi",
        }
    }

    mock_instance = mock_exam_reg.return_value
    mock_instance.save.side_effect = Exception("Database error")

    with patch("module.commands.reminder.get_locale", return_value="Errore duplicato"):
        reminder_confermato_handler(mock_update, mock_context)

        mock_context.bot.editMessageText.assert_called_once()
        assert (
            mock_context.bot.editMessageText.call_args.kwargs["text"]
            == "Errore duplicato"
        )


@patch("module.commands.reminder.DbManager.select_from")
@patch("module.commands.reminder.ExamRegistration")
def test_reminder_confermato_handler_duplicate(mock_exam_reg, mock_select):
    """Test reminder_confermato_handler() quando il reminder è già presente nel DB."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"
    mock_update.callback_query.message.chat_id = 12345
    mock_update.callback_query.message.message_id = 67890

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {
            "appello": "2026-06-15",
            "insegnamento": "Analisi",
            "professore": "Rossi",
        }
    }

    mock_select.return_value = ["esiste_gia"]

    mock_instance = mock_exam_reg.return_value

    with patch("module.commands.reminder.get_locale", return_value="Già presente"):
        reminder_confermato_handler(mock_update, mock_context)

        mock_select.assert_called_once()

        mock_instance.save.assert_not_called()

        mock_context.bot.editMessageText.assert_called_once_with(
            text="Già presente", chat_id=12345, message_id=67890, parse_mode='Markdown'
        )

        assert not mock_context.user_data.get("reminder")


@pytest.mark.parametrize(
    "days_offset, expected_text, should_save",
    [
        (20, "Registrazione confermata", True),
        (14, "Registrazione confermata", True),
        (10, "Registrazione confermata", True),
        (5, "Registrazione confermata", True),
        (2, "Troppo tardi", False),
        (0, "Troppo tardi", False),
        (-5, "Troppo tardi", False),
    ],
)
@patch("module.commands.reminder.ExamRegistration")
@patch("module.commands.reminder.DbManager.select_from")
@patch("module.commands.reminder.date")
def test_reminder_confermato_handler_time_thresholds(
    mock_date, mock_select, mock_exam_reg, days_offset, expected_text, should_save
):
    """Test parametrizzato per verificare le soglie temporali di registrazione esami."""

    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"
    mock_context = MagicMock()

    base_date = datetime(2026, 6, 10)
    mock_date.today.return_value = base_date.date()

    appello_date = base_date + timedelta(days=days_offset)
    appello_str = appello_date.strftime("%d/%m/%Y")

    mock_context.user_data = {
        "reminder": {
            "appello": appello_str,
            "insegnamento": "Analisi",
            "professore": "Rossi",
        }
    }

    mock_select.return_value = []
    mock_instance = mock_exam_reg.return_value

    with patch("module.commands.reminder.get_locale", return_value=expected_text):
        reminder_confermato_handler(mock_update, mock_context)

        if should_save:
            mock_instance.save.assert_called_once()
        else:
            mock_instance.save.assert_not_called()

        mock_context.bot.editMessageText.assert_called_once_with(
            text=expected_text,
            chat_id=mock_update.callback_query.message.chat_id,
            message_id=mock_update.callback_query.message.message_id,
            parse_mode='Markdown',
        )


# ---- reminder_annullato_handler() in module/commands/reminder.py


def test_reminder_annullato_handler():
    """Test reminder_annullato_handler() clears user_data and aborts."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {"appello": "15-06-2026"}}

    with patch("module.commands.reminder.get_locale", return_value="Annullato"):
        reminder_annullato_handler(mock_update, mock_context)

        assert "reminder" not in mock_context.user_data
        mock_context.bot.editMessageText.assert_called_once()


# ---- reminder_button_appello() in module/commands/reminder.py


@patch("module.commands.reminder.Exam.find")
def test_reminder_button_appello_parses_dates(mock_exam_find):
    """Test reminder_button_appello() properly extracts ast.literal_eval dates."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"
    mock_chat_id = 123
    mock_message_id = 456

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {
            "insegnamento": "Analisi",
            "professore": "Rossi",
            "sessione": "prima",
        }
    }

    # Simulate database returning a stringified list of dates
    mock_exam = MagicMock(docenti="Rossi", prima="['15-06-2026', '01-07-2026']")
    mock_exam_find.return_value = [mock_exam]

    with patch("module.commands.reminder.get_locale", return_value="Scegli data"):
        reminder_button_appello(
            mock_update, mock_context, mock_chat_id, mock_message_id
        )

        mock_context.bot.editMessageText.assert_called_once()
        kwargs = mock_context.bot.editMessageText.call_args.kwargs
        reply_markup = kwargs["reply_markup"]

        # Verify the inline keyboard created buttons for the parsed dates
        assert reply_markup is not None
        assert (
            reply_markup.inline_keyboard[0][0].callback_data == "rem_appello_15-06-2026"
        )
        assert (
            reply_markup.inline_keyboard[1][0].callback_data == "rem_appello_01-07-2026"
        )


@patch("module.commands.reminder.Exam.find")
@patch("module.commands.reminder.get_locale")
# Rimosso il patch di TEXT_IDS
def test_reminder_button_appello_no_dates(mock_get_locale, mock_exam_find):
    '''Testa reminder_button_appello() nel caso in cui non ci sono appelli disponibili'''

    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {
            "insegnamento": "Analisi I",
            "professore": "Rossi",
            "sessione": "prima",
        }
    }

    mock_exam_find.return_value = []
    mock_get_locale.return_value = "Non ci sono date disponibili."

    chat_id = 12345
    message_id = 67890

    reminder_button_appello(mock_update, mock_context, chat_id, message_id)

    mock_get_locale.assert_called_with("it", TEXT_IDS.REMINDER_NO_EXAM_DATE)

    mock_context.bot.editMessageText.assert_called_once_with(
        text="Non ci sono date disponibili.",
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=None,
    )


# ---- general in module/commands/reminder.py


def test_empty_context_early_returns():
    """Test early returns across various handlers when context is missing."""
    mock_update = MagicMock()
    mock_context = MagicMock()
    mock_context.user_data = {}

    reminder_input_insegnamento(mock_update, mock_context)
    reminder_prof_handler(mock_update, mock_context)
    reminder_sessione_handler(mock_update, mock_context)
    reminder_appello_handler(mock_update, mock_context)

    mock_context.bot.send_message.assert_not_called()
    mock_context.bot.editMessageText.assert_not_called()


# ---- reminder_send_message in module/commands/reminder.py


GET_LOCALE_PATH = 'module.utils.multi_lang_utils.get_locale'
TEXT_IDS_PATH = 'module.data.vars.TEXT_IDS'
PLACE_HOLDER_PATH = 'module.data.vars.PLACE_HOLDER'


@pytest.mark.parametrize(
    "exam_date, target_1, target_2, expected_call_count",
    [
        ("10-04-2026", "10-04-2026", "30-03-2026", 1),
        ("30-03-2026", "10-04-2026", "30-03-2026", 1),
        ("01-05-2026", "10-04-2026", "30-03-2026", 0),
    ],
)
def test_reminder_send_message_logic(
    exam_date, target_1, target_2, expected_call_count
):
    '''Testa la logica di invio del messaggio in maniera parametrizzata'''
    mock_context = MagicMock()
    reminders = [
        {
            'studenti': 123456,
            'insegnamento': 'Analisi',
            'docenti': 'Prof. X',
            'data': exam_date,
            'lingua': 'it',
        }
    ]

    with patch(GET_LOCALE_PATH) as mock_get_locale, patch(TEXT_IDS_PATH), patch(
        PLACE_HOLDER_PATH, "{}"
    ):

        mock_get_locale.return_value = "Info: {} {} {}"

        reminder_send_message(reminders, mock_context, target_1, target_2)

        assert mock_context.bot.send_message.call_count == expected_call_count

        if expected_call_count > 1:
            sent_text = mock_context.bot.send_message.call_args[1]['text']
            assert "Analisi" in sent_text
            assert exam_date in sent_text


def test_reminder_send_message_exception():
    """Testa la gestione dell'errore se l'invio fallisce"""
    mock_context = MagicMock()
    reminders = [{'studenti': 1, 'data': "01-01-2026", 'lingua': 'it'}]

    mock_context.bot.send_message.side_effect = Exception("Bot blocked")

    with patch(GET_LOCALE_PATH) as mock_get_locale, patch(TEXT_IDS_PATH), patch(
        PLACE_HOLDER_PATH, "{}"
    ):

        mock_get_locale.return_value = "Test {} {} {}"

        reminder_send_message(reminders, mock_context, "01-01-2026", "02-02-2026")

        assert mock_context.bot.send_message.called


@patch("module.commands.reminder.DbManager.delete_from")
def test_reminder_send_message_deletes_on_second_target(mock_delete):
    """Test reminder_send_message() elimina il record al secondo avviso."""
    mock_context = MagicMock()
    exam_date = "10-04-2026"
    reminders = [
        {
            'studenti': 123456,
            'insegnamento': 'Analisi',
            'docenti': 'Prof. Test',
            'data': exam_date,
            'lingua': 'it',
        }
    ]

    target_1 = "30-03-2026"
    target_2 = exam_date

    with patch("module.utils.multi_lang_utils.get_locale", return_value="Test"):
        reminder_send_message(reminders, mock_context, target_1, target_2)

        mock_context.bot.send_message.assert_called_once()
        mock_delete.assert_called_once_with(
            table_name="exams_reg",
            where="studenti = ? AND insegnamento = ? AND docenti = ?",
            where_args=("123456", "Analisi", "Prof. Test"),
        )
