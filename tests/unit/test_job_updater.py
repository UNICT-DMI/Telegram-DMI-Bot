# -*- coding: utf-8 -*-
"""Test suite for the scrapers update job."""

from unittest.mock import MagicMock, patch

from module.data.exam import Exam
from module.job_updater import updater_lep


@patch('module.job_updater.TimetableSlot')
@patch('module.job_updater.Professor')
@patch('module.job_updater.Exam')
def test_updater_lep_runs_every_scraper_when_one_fails(
    mock_exam, mock_professor, mock_timetable_slot
):
    mock_exam.scrape.side_effect = AttributeError("table not found")

    updater_lep(MagicMock())

    mock_professor.scrape.assert_called_once_with(delete=True)
    mock_timetable_slot.scrape.assert_called_once_with(delete=True)


@patch.object(Exam, 'bulk_save')
@patch.object(Exam, 'delete_all')
@patch('module.data.exam.requests.get')
def test_exam_scrape_skips_pages_without_table(
    mock_get, mock_delete_all, mock_bulk_save
):
    mock_get.return_value = MagicMock(text="<html><body></body></html>")

    Exam.scrape("126", delete=True)

    mock_delete_all.assert_called_once()
    mock_bulk_save.assert_called_once_with([])
