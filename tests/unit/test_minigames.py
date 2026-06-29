# -*- coding: utf-8 -*-
"""Test suite for the /minigames command (Tris)."""

from unittest.mock import MagicMock, patch

import pytest

import module.commands.tris as tris
from module.commands.tris import (
    CPU,
    EMPTY,
    GLYPHS,
    PLAYER,
    STUDENT_ICONS,
    WIN_GLYPHS,
    _ai_move,
    _board_keyboard,
    _minimax,
    _mode_keyboard,
    _winner,
    _winning_line,
    tictactoe_handler,
)
from module.data import DbManager

# ---- _winner()


def test_winner_detects_row():
    board = list("xxx" "o-o" "---")
    assert _winner(board) == PLAYER


def test_winner_detects_column():
    board = list("o--" "o-x" "o-x")
    assert _winner(board) == CPU


def test_winner_detects_diagonal():
    board = list("x-o" "-x-" "o-x")
    assert _winner(board) == PLAYER


def test_winner_none_on_incomplete_board():
    assert _winner(list("xo-" "-x-" "--o")) is None
    assert _winner([EMPTY] * 9) is None


# ---- _ai_move()


def test_easy_returns_legal_cell():
    board = list("xo-" "xo-" "---")
    empty = {2, 5, 6, 7, 8}
    for _ in range(20):
        assert _ai_move(list(board), 'e') in empty


def test_medium_takes_immediate_win():
    # CPU (o) can complete the top row at cell 2
    board = list("oo-" "xx-" "---")
    assert _ai_move(board, 'm') == 2


def test_medium_blocks_player_win():
    # player (x) threatens the top row at cell 2, CPU must block there
    board = list("xx-" "o--" "o--")
    assert _ai_move(board, 'm') == 2


def test_hard_takes_immediate_win():
    board = list("oo-" "xx-" "---")
    assert _ai_move(board, 'h') == 2


def test_hard_blocks_player_win():
    board = list("xx-" "o--" "---")
    assert _ai_move(board, 'h') == 2


def test_hard_never_loses_from_empty_board():
    """Minimax playing both sides must always end in a draw, never a CPU loss."""
    board = [EMPTY] * 9
    turn = PLAYER  # player moves first
    while _winner(board) is None and EMPTY in board:
        if turn == CPU:
            move = _ai_move(board, 'h')
        else:
            move = _minimax(list(board), PLAYER)[1]
        board[move] = turn
        turn = CPU if turn == PLAYER else PLAYER
    assert _winner(board) != CPU
    assert _winner(board) != PLAYER  # optimal play on both sides is a draw


# ---- tictactoe_handler()


def _make_query(data):
    query = MagicMock()
    query.data = data
    query.from_user.language_code = "it"
    query.message.chat_id = 1
    query.message.message_id = 2
    update = MagicMock()
    update.callback_query = query
    return update, query


def test_handler_new_game_renders_board():
    update, query = _make_query("ttt_new_e")
    context = MagicMock()
    with patch("module.commands.tris.get_locale", return_value="turn"):
        tictactoe_handler(update, context)
    query.answer.assert_called_once()
    context.bot.editMessageText.assert_called_once()


def test_handler_winning_move_shows_result():
    update, query = _make_query("ttt_mv_h_x_xx-oo----_2")
    context = MagicMock()
    with patch("module.commands.tris.get_locale", return_value="win") as mock_locale:
        from module.data.vars import TEXT_IDS

        mock_locale.side_effect = lambda loc, tid: tid.name
        tictactoe_handler(update, context)
    context.bot.editMessageText.assert_called_once()
    sent_text = context.bot.editMessageText.call_args.kwargs["text"]
    assert sent_text == TEXT_IDS.TRIS_WIN_TEXT_ID.name


def test_handler_ignores_taken_cell():
    update, query = _make_query("ttt_mv_e_x_x--------_0")
    context = MagicMock()
    tictactoe_handler(update, context)
    query.answer.assert_called_once()
    context.bot.editMessageText.assert_not_called()


# ---- winning line / rendering


def test_winning_line_returns_indices():
    assert _winning_line(list("xxx" "o-o" "---")) == (0, 1, 2)
    assert _winning_line(list("o--" "o-x" "o-x")) == (0, 3, 6)
    assert _winning_line(list("xo-" "-x-" "--o")) is None


def test_board_keyboard_marks_winning_cells_green():
    board = list("xxx" "oo-" "---")
    keyboard = _board_keyboard(board, 'e', PLAYER, False, (0, 1, 2))
    assert [btn.text for btn in keyboard[0]] == [WIN_GLYPHS[PLAYER]] * 3
    assert keyboard[1][0].text == GLYPHS[CPU]  # non-winning cell stays normal


def test_player_symbol_swaps_rendered_glyphs():
    board = list("x" "o" "-------")
    as_x = _board_keyboard(board, 'e', PLAYER, False)
    assert (as_x[0][0].text, as_x[0][1].text) == (GLYPHS[PLAYER], GLYPHS[CPU])
    # when the human plays as O, their mark renders as ⭕ and the CPU's as ❌
    as_o = _board_keyboard(board, 'e', CPU, False)
    assert (as_o[0][0].text, as_o[0][1].text) == (GLYPHS[CPU], GLYPHS[PLAYER])


# ---- vs player (online matchmaking, persisted in the DB)


def _queue():
    return DbManager.select_from(table_name="minigames_queue")


def _game_rows():
    return DbManager.select_from(table_name="tris_game")


def _load_game():
    rows = _game_rows()
    return tris._row_to_game(rows[0]) if rows else None


def _set_board(game_id, board):
    conn, cur = DbManager.get_db()
    cur.execute(
        "UPDATE tris_game SET board = ? WHERE game_id = ?", (board, int(game_id))
    )
    conn.commit()
    cur.close()
    conn.close()


def _backdate(user_id, seconds):
    conn, cur = DbManager.get_db()
    cur.execute(
        "UPDATE minigames_queue SET queued_at = queued_at - ? WHERE user_id = ?",
        (seconds, user_id),
    )
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture(autouse=True)
def _reset_pvp_state():
    DbManager.delete_from("minigames_queue")
    DbManager.delete_from("tris_game")
    yield
    DbManager.delete_from("minigames_queue")
    DbManager.delete_from("tris_game")


def _pvp_query(data, user_id):
    update, query = _make_query(data)
    query.from_user.id = user_id
    query.from_user.first_name = f"User{user_id}"
    return update, query


def _enqueue(user_id, chat_id):
    """Drive a ttt_pvp click for a player and return its mock context."""
    update, query = _pvp_query("ttt_pvp", user_id)
    query.message.chat_id = chat_id
    context = MagicMock()
    with patch(
        "module.commands.tris.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        tictactoe_handler(update, context)
    return context


def test_mode_keyboard_pvp_button_has_student_icon():
    with patch(
        "module.commands.tris.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        keyboard = _mode_keyboard("it")
    pvp_button = keyboard[1][0]
    assert pvp_button.callback_data == "ttt_pvp"
    assert any(pvp_button.text.startswith(icon) for icon in STUDENT_ICONS)


def test_first_player_is_queued():
    context = _enqueue(100, chat_id=10)
    assert [r["user_id"] for r in _queue()] == [100]
    assert _game_rows() == []
    context.bot.editMessageText.assert_called_once()


def test_same_player_clicking_twice_stays_queued():
    _enqueue(100, chat_id=10)
    _enqueue(100, chat_id=10)
    assert [r["user_id"] for r in _queue()] == [100]
    assert _game_rows() == []


def test_second_player_starts_a_game_and_updates_both_boards():
    _enqueue(100, chat_id=10)
    context = _enqueue(200, chat_id=20)
    assert _queue() == []
    assert len(_game_rows()) == 1
    game = _load_game()
    assert {p["user_id"] for p in game["players"].values()} == {100, 200}
    # both players' messages are refreshed by the pairing render
    assert context.bot.editMessageText.call_count == 2


def test_four_players_form_two_independent_games():
    for user_id, chat_id in ((100, 10), (200, 20), (300, 30), (400, 40)):
        _enqueue(user_id, chat_id)
    assert _queue() == []
    pairings = {frozenset((row["x_user_id"], row["o_user_id"])) for row in _game_rows()}
    assert pairings == {frozenset({100, 200}), frozenset({300, 400})}


def test_stale_waiter_is_not_paired():
    _enqueue(100, chat_id=10)
    _backdate(100, tris.WAITING_TIMEOUT + 1)
    _enqueue(200, chat_id=20)
    # 100 is too old to pair with, so 200 waits instead of starting a game with a ghost
    assert _game_rows() == []
    assert 200 in [r["user_id"] for r in _queue()]


def test_expire_waiters_notifies_and_drops_stale_entries():
    _enqueue(100, chat_id=10)
    _backdate(100, tris.WAITING_TIMEOUT + 1)
    context = MagicMock()
    with patch(
        "module.commands.tris.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        tris.expire_tris_waiters(context)
    assert _queue() == []
    context.bot.editMessageText.assert_called_once()


def test_expire_waiters_keeps_fresh_entries():
    _enqueue(100, chat_id=10)
    context = MagicMock()
    tris.expire_tris_waiters(context)
    assert [r["user_id"] for r in _queue()] == [100]
    context.bot.editMessageText.assert_not_called()


def test_cancel_removes_player_from_queue():
    _enqueue(100, chat_id=10)
    update, query = _pvp_query("ttt_pcancel", 100)
    with patch(
        "module.commands.tris.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        tictactoe_handler(update, MagicMock())
    assert _queue() == []


def _active_game():
    _enqueue(100, chat_id=10)
    _enqueue(200, chat_id=20)
    return _load_game()


def _move(game, user_id, cell):
    update, query = _pvp_query(f"ttt_pmv_{game['id']}_{cell}", user_id)
    context = MagicMock()
    with patch(
        "module.commands.tris.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        tictactoe_handler(update, context)
    return query, context


def test_pvp_move_rejects_unknown_game():
    query, context = _move({"id": "999"}, 100, 0)
    assert query.answer.call_args.kwargs.get("show_alert") is True
    context.bot.editMessageText.assert_not_called()


def test_pvp_move_rejects_non_participant():
    game = _active_game()
    query, context = _move(game, 999, 0)
    assert query.answer.call_args.kwargs.get("show_alert") is True
    context.bot.editMessageText.assert_not_called()


def test_pvp_move_rejects_wrong_turn():
    game = _active_game()
    waiting_mark = CPU  # X moves first; the O player tapping is out of turn
    o_player_id = game["players"][waiting_mark]["user_id"]
    query, context = _move(game, o_player_id, 0)
    assert query.answer.call_args.kwargs.get("show_alert") is True
    context.bot.editMessageText.assert_not_called()


def test_pvp_move_applies_and_alternates_turn():
    game = _active_game()
    x_player_id = game["players"][PLAYER]["user_id"]
    _move(game, x_player_id, 0)
    board = _load_game()["board"]
    assert board[0] == PLAYER
    assert board.count(PLAYER) == 1


def test_pvp_winning_move_ends_game():
    game = _active_game()
    _set_board(game["id"], "xx-oo----")
    x_player_id = game["players"][PLAYER]["user_id"]
    _move(game, x_player_id, 2)  # completes the top row
    assert _game_rows() == []  # finished games are dropped


def test_pvp_board_keyboard_encodes_game_id():
    game = {"id": "7", "board": list("x--------"), "players": {}}
    keyboard = tris._pvp_board_keyboard(game, True, None)
    assert keyboard[0][0].text == GLYPHS[PLAYER]
    assert keyboard[0][1].callback_data == "ttt_pmv_7_1"


def test_deliver_falls_back_to_a_new_message_and_persists_id():
    from telegram.error import TelegramError

    game = _active_game()
    player = game["players"][PLAYER]
    context = MagicMock()
    context.bot.editMessageText.side_effect = TelegramError("message to edit not found")
    context.bot.sendMessage.return_value = MagicMock(message_id=99)

    tris._deliver(context, game["id"], PLAYER, player, "text", [])

    context.bot.sendMessage.assert_called_once()
    assert player["message_id"] == 99  # later moves now target the new message
    assert _load_game()["players"][PLAYER]["message_id"] == 99  # persisted in the DB


def test_deliver_keeps_message_on_not_modified():
    from telegram.error import TelegramError

    game = _active_game()
    player = game["players"][PLAYER]
    original = player["message_id"]
    context = MagicMock()
    context.bot.editMessageText.side_effect = TelegramError("Message is not modified")

    tris._deliver(context, game["id"], PLAYER, player, "text", [])

    context.bot.sendMessage.assert_not_called()
    assert player["message_id"] == original
