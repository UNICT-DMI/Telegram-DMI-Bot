# -*- coding: utf-8 -*-
"""Test suite for the /aulario command and its scraper."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from module.commands.aulario import create_calendar
from module.data.db_manager import DbManager
from module.data.timetable_slot import TimetableSlot

AULARIO_HTML = """
<table>
  <thead><tr>
    <td>Venerdì, 09/10/2026</td>
    <td colspan="2">15:00</td><td colspan="2">16:00</td>
  </tr></thead>
  <tbody><tr>
    <td>Aula F - Blocco 3</td>
    <td colspan="3">Software Quality and Project Development [Borzì]</td><td></td>
  </tr></tbody>
</table>
<table>
  <thead><tr>
    <td>Sabato, 10/10/2026</td>
    <td colspan="2">15:00</td><td colspan="2">16:00</td>
  </tr></thead>
  <tbody><tr>
    <td>Aula 1</td><td></td><td></td><td colspan="2">Algebra []</td>
  </tr></tbody>
</table>
"""


class FakeDate(date):
    """date whose today() is fixed to Friday 2026-10-02"""

    @classmethod
    def today(cls):
        return cls(2026, 10, 2)


@pytest.fixture(name="fixed_today")
def fixture_fixed_today(monkeypatch):
    monkeypatch.setattr('module.commands.aulario.date', FakeDate)


def callbacks(markup) -> list:
    return [b.callback_data for row in markup.inline_keyboard for b in row]


@patch.object(TimetableSlot, 'bulk_save')
@patch.object(TimetableSlot, 'delete_all')
@patch('module.data.timetable_slot.DbManager')
@patch('module.data.timetable_slot.requests.get')
def test_scrape_stores_the_date_of_each_table(mock_get, mock_db, _, mock_bulk_save):
    mock_get.return_value = MagicMock(text=AULARIO_HTML)
    mock_db.count_from.return_value = 0

    TimetableSlot.scrape(delete=True)

    slots = mock_bulk_save.call_args[0][0]
    assert [(s.nome, s.giorno, s.ora_inizio, s.ora_fine, s.aula) for s in slots] == [
        (
            "Software Quality and Project Development (Borzì)",
            "2026-10-09",
            "15:00",
            "16:00",
            "Aula F - Blocco 3",
        ),
        ("Algebra ", "2026-10-10", "16:00", "16:30", "Aula 1"),
    ]


def test_get_last_day_ignores_rows_with_a_day_offset(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    get_db = DbManager.get_db
    monkeypatch.setattr(DbManager, "get_db", staticmethod(lambda: get_db(db_path)))
    DbManager.query_from_string(
        "CREATE TABLE timetable_slots (ID INTEGER PRIMARY KEY, nome VARCHAR(255),"
        " giorno INT(4), ora_inizio VARCHAR(255), ora_fine VARCHAR(255), aula VARCHAR(255))"
    )
    assert TimetableSlot.get_last_day() is None

    TimetableSlot(ID=1, nome="old", giorno=54).save()
    assert TimetableSlot.get_last_day() is None

    TimetableSlot(ID=2, nome="new", giorno="2026-11-30").save()
    TimetableSlot(ID=3, nome="new", giorno="2026-10-09").save()
    assert TimetableSlot.get_last_day() == date(2026, 11, 30)


@pytest.mark.usefixtures("fixed_today")
def test_create_calendar_offers_days_from_today_to_last_day():
    data = callbacks(create_calendar(date(2026, 10, 9)))

    assert [d for d in data if d.startswith("cal_")] == [
        f"cal_2026-10-0{day}" for day in range(2, 10)
    ]
    assert not [d for d in data if d.startswith("m_")]


@pytest.mark.usefixtures("fixed_today")
def test_create_calendar_navigates_to_next_month():
    current = callbacks(create_calendar(date(2026, 11, 3)))
    assert "m_n_2026_10_2026-11-03" in current
    assert "cal_2026-10-31" in current

    following = callbacks(create_calendar(date(2026, 11, 3), 2026, 11))
    assert [d for d in following if d.startswith("cal_")] == [
        "cal_2026-11-01",
        "cal_2026-11-02",
        "cal_2026-11-03",
    ]
    assert "m_p_2026_11_2026-11-03" in following
    assert "m_n_2026_11_2026-11-03" not in following
