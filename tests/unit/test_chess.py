# -*- coding: utf-8 -*-
"""Test suite for the chess mini game (player vs player)."""

from unittest.mock import MagicMock, patch

import chess
import pytest

import module.commands.chess_game as chess_game
from module.commands.chess_game import (
    BLACK,
    KING_GLYPHS,
    PIECE_GLYPHS,
    WHITE,
    _board_keyboard,
    _captured_symbol,
    _display_squares,
    _game_result,
    chess_handler,
)
from module.commands.minigames import _hub_keyboard
from module.data import DbManager


def _make_query(data):
    query = MagicMock()
    query.data = data
    query.from_user.language_code = "it"
    query.message.chat_id = 1
    query.message.message_id = 2
    update = MagicMock()
    update.callback_query = query
    return update, query


# ---- board geometry / rendering


def test_display_squares_orient_white_at_bottom():
    grid = _display_squares(WHITE)
    assert grid[0][0] == chess.A8  # top-left is a8 for White
    assert grid[7][0] == chess.A1  # bottom-left is a1
    assert grid[7][7] == chess.H1


def test_display_squares_orient_black_at_bottom():
    grid = _display_squares(BLACK)
    assert grid[0][0] == chess.H1  # board is flipped for Black
    assert grid[7][7] == chess.A8


def test_board_keyboard_renders_starting_pieces():
    board = chess.Board()
    game = {"id": "1"}
    keyboard = _board_keyboard(game, board, WHITE, tappable=False, selected=None)
    # top row from White's view is Black's back rank
    assert keyboard[0][0].text == PIECE_GLYPHS['r']
    assert keyboard[0][4].text == PIECE_GLYPHS['k']
    assert keyboard[7][4].text == PIECE_GLYPHS['K']  # White king on e1


def test_board_keyboard_own_pieces_are_selectable_when_tappable():
    board = chess.Board()
    game = {"id": "5"}
    keyboard = _board_keyboard(game, board, WHITE, tappable=True, selected=None)
    e2_button = keyboard[6][4]  # e2 pawn for White
    assert e2_button.callback_data == f"chess_sel_5_{chess.E2}"
    # Black's pieces are not tappable on White's turn
    assert keyboard[1][4].callback_data == "NONE"


def test_board_keyboard_not_tappable_disables_everything():
    board = chess.Board()
    keyboard = _board_keyboard({"id": "1"}, board, WHITE, tappable=False, selected=None)
    assert all(btn.callback_data == "NONE" for row in keyboard for btn in row)


def test_board_keyboard_highlights_selected_piece_moves():
    board = chess.Board()
    game = {"id": "9"}
    keyboard = _board_keyboard(game, board, WHITE, tappable=True, selected=chess.E2)
    flat = {btn.callback_data: btn.text for row in keyboard for btn in row}
    # e3 and e4 are the pawn's legal destinations
    assert flat[f"chess_mv_9_{chess.E2}_{chess.E3}"] == chess_game.MOVE_DOT
    assert flat[f"chess_mv_9_{chess.E2}_{chess.E4}"] == chess_game.MOVE_DOT
    # tapping the selected pawn again clears the selection
    assert "chess_open_9" in flat


def test_board_keyboard_marks_capture_targets_red():
    # White pawn e4, Black pawn d5: e4xd5 is the only capture available to e4
    board = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2")
    keyboard = _board_keyboard(
        {"id": "3"}, board, WHITE, tappable=True, selected=chess.E4
    )
    flat = {btn.callback_data: btn.text for row in keyboard for btn in row}
    assert flat[f"chess_mv_3_{chess.E4}_{chess.D5}"] == chess_game.CAPTURE_DOT


# ---- captured-piece detection


def test_captured_symbol_normal_capture():
    board = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2")
    move = chess.Move(chess.E4, chess.D5)
    assert _captured_symbol(board, move) == 'p'


def test_captured_symbol_en_passant():
    board = chess.Board("rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3")
    move = chess.Move(chess.E5, chess.F6)
    assert board.is_en_passant(move)
    assert _captured_symbol(board, move) == 'p'


def test_captured_symbol_none_for_quiet_move():
    board = chess.Board()
    assert _captured_symbol(board, chess.Move(chess.E2, chess.E4)) is None


# ---- game result


def test_game_result_ongoing():
    assert _game_result(chess.Board(), None) is None


def test_game_result_checkmate_names_winner():
    board = chess.Board("6k1/5ppp/8/8/8/8/8/3QK3 w - - 0 1")
    board.push(chess.Move(chess.D1, chess.D8))  # back-rank mate
    assert board.is_checkmate()
    assert _game_result(board, None) == ('checkmate', WHITE, BLACK)


def test_game_result_resign():
    assert _game_result(chess.Board(), WHITE) == ('resign', BLACK, WHITE)


# ---- vs player (online matchmaking, persisted in the DB)


def _queue():
    return DbManager.select_from(table_name="minigames_queue")


def _game_rows():
    return DbManager.select_from(table_name="chess_game")


def _load_game():
    rows = _game_rows()
    return chess_game._row_to_game(rows[0]) if rows else None


def _set_fen(game_id, fen, **cols):
    conn, cur = DbManager.get_db()
    cur.execute("UPDATE chess_game SET fen = ? WHERE game_id = ?", (fen, int(game_id)))
    for col, val in cols.items():
        cur.execute(
            f"UPDATE chess_game SET {col} = ? WHERE game_id = ?", (val, int(game_id))
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
    DbManager.delete_from("chess_game")
    DbManager.delete_from("minigames_settings")
    yield
    DbManager.delete_from("minigames_queue")
    DbManager.delete_from("chess_game")
    DbManager.delete_from("minigames_settings")


def _pvp_query(data, user_id):
    update, query = _make_query(data)
    query.from_user.id = user_id
    query.from_user.first_name = f"User{user_id}"
    return update, query


def _enqueue(user_id, chat_id):
    update, query = _pvp_query("chess_play", user_id)
    query.message.chat_id = chat_id
    context = MagicMock()
    with patch(
        "module.commands.chess_game.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        chess_handler(update, context)
    return context


def test_hub_keyboard_hides_chess_button_while_in_beta():
    # chess is still a work in progress; its hub button is commented out for now
    with patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        keyboard = _hub_keyboard("it")
    assert not any(btn.callback_data == "chess_play" for row in keyboard for btn in row)


def test_first_player_is_queued():
    context = _enqueue(100, chat_id=10)
    assert [r["user_id"] for r in _queue()] == [100]
    assert _game_rows() == []
    context.bot.editMessageText.assert_called_once()


def test_second_player_starts_a_game_and_updates_both_boards():
    _enqueue(100, chat_id=10)
    context = _enqueue(200, chat_id=20)
    assert _queue() == []
    assert len(_game_rows()) == 1
    game = _load_game()
    assert {p["user_id"] for p in game["players"].values()} == {100, 200}
    assert game["fen"] == chess.STARTING_FEN
    assert context.bot.editMessageText.call_count == 2  # both boards refreshed


def test_stale_waiter_is_not_paired():
    _enqueue(100, chat_id=10)
    _backdate(100, chess_game.WAITING_TIMEOUT + 1)
    _enqueue(200, chat_id=20)
    assert _game_rows() == []
    assert 200 in [r["user_id"] for r in _queue()]


def test_cancel_removes_player_from_queue():
    _enqueue(100, chat_id=10)
    update, query = _pvp_query("chess_pcancel", 100)
    with patch(
        "module.commands.chess_game.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        chess_handler(update, MagicMock())
    assert _queue() == []


def test_expire_waiters_notifies_and_drops_stale_entries():
    _enqueue(100, chat_id=10)
    _backdate(100, chess_game.WAITING_TIMEOUT + 1)
    context = MagicMock()
    with patch(
        "module.commands.chess_game.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        chess_game.expire_chess_waiters(context)
    assert _queue() == []
    context.bot.editMessageText.assert_called_once()


def test_expire_waiters_keeps_fresh_entries():
    _enqueue(100, chat_id=10)
    context = MagicMock()
    chess_game.expire_chess_waiters(context)
    assert [r["user_id"] for r in _queue()] == [100]
    context.bot.editMessageText.assert_not_called()


def _active_game():
    _enqueue(100, chat_id=10)
    _enqueue(200, chat_id=20)
    return _load_game()


def _move(game, user_id, from_sq, to_sq):
    update, query = _pvp_query(f"chess_mv_{game['id']}_{from_sq}_{to_sq}", user_id)
    context = MagicMock()
    with patch(
        "module.commands.chess_game.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        chess_handler(update, context)
    return query, context


def test_move_rejects_unknown_game():
    query, context = _move({"id": "999"}, 100, chess.E2, chess.E4)
    assert query.answer.call_args.kwargs.get("show_alert") is True
    context.bot.editMessageText.assert_not_called()


def test_move_rejects_non_participant():
    game = _active_game()
    query, context = _move(game, 999, chess.E2, chess.E4)
    assert query.answer.call_args.kwargs.get("show_alert") is True
    context.bot.editMessageText.assert_not_called()


def test_move_rejects_wrong_turn():
    game = _active_game()
    black_id = game["players"][BLACK]["user_id"]  # White moves first
    query, context = _move(game, black_id, chess.E7, chess.E5)
    assert query.answer.call_args.kwargs.get("show_alert") is True
    context.bot.editMessageText.assert_not_called()


def test_legal_move_applies_and_alternates_turn():
    game = _active_game()
    white_id = game["players"][WHITE]["user_id"]
    _move(game, white_id, chess.E2, chess.E4)
    board = chess.Board(_load_game()["fen"])
    assert board.turn == chess.BLACK
    assert board.piece_at(chess.E4) is not None


def test_illegal_move_is_ignored():
    game = _active_game()
    white_id = game["players"][WHITE]["user_id"]
    query, context = _move(game, white_id, chess.E2, chess.E5)  # pawn can't jump three
    query.answer.assert_called_once_with()  # answered without an alert
    context.bot.editMessageText.assert_not_called()
    assert _load_game()["fen"] == chess.STARTING_FEN  # unchanged


def test_capture_is_recorded_against_the_capturing_player():
    game = _active_game()
    white_id = game["players"][WHITE]["user_id"]
    _set_fen(
        game["id"],
        "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2",
    )
    _move(game, white_id, chess.E4, chess.D5)
    assert _load_game()["white_captured"] == 'p'


def test_checkmate_ends_and_drops_the_game():
    game = _active_game()
    white_id = game["players"][WHITE]["user_id"]
    _set_fen(game["id"], "6k1/5ppp/8/8/8/8/8/3QK3 w - - 0 1")
    query, context = _move(game, white_id, chess.D1, chess.D8)
    assert _game_rows() == []  # finished games are dropped
    context.bot.editMessageText.assert_called()  # both players see the result


def test_resign_drops_game_and_refreshes_both():
    game = _active_game()
    black_id = game["players"][BLACK]["user_id"]
    update, query = _pvp_query(f"chess_resign_{game['id']}", black_id)
    context = MagicMock()
    with patch(
        "module.commands.chess_game.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        chess_handler(update, context)
    assert _game_rows() == []
    assert context.bot.editMessageText.call_count == 2


def test_resign_rejects_non_participant():
    game = _active_game()
    update, query = _pvp_query(f"chess_resign_{game['id']}", 999)
    context = MagicMock()
    with patch(
        "module.commands.chess_game.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        chess_handler(update, context)
    assert query.answer.call_args.kwargs.get("show_alert") is True
    assert len(_game_rows()) == 1  # game untouched


# ---- selection (own message redraw, no DB change)


def test_select_highlights_moves_for_current_player():
    game = _active_game()
    white_id = game["players"][WHITE]["user_id"]
    update, query = _pvp_query(f"chess_sel_{game['id']}_{chess.E2}", white_id)
    context = MagicMock()
    with patch(
        "module.commands.chess_game.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        chess_handler(update, context)
    context.bot.editMessageText.assert_called_once()
    markup = context.bot.editMessageText.call_args.kwargs["reply_markup"]
    callbacks = {btn.callback_data for row in markup.inline_keyboard for btn in row}
    assert f"chess_mv_{game['id']}_{chess.E2}_{chess.E4}" in callbacks
    assert _load_game()["fen"] == chess.STARTING_FEN  # selection persists nothing


def test_select_rejected_for_player_off_turn():
    game = _active_game()
    black_id = game["players"][BLACK]["user_id"]
    update, query = _pvp_query(f"chess_sel_{game['id']}_{chess.E7}", black_id)
    context = MagicMock()
    with patch(
        "module.commands.chess_game.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        chess_handler(update, context)
    assert query.answer.call_args.kwargs.get("show_alert") is True
    context.bot.editMessageText.assert_not_called()


# ---- names and captured display


def test_player_label_uses_king_glyph_and_name():
    game = {"players": {WHITE: {"name": "🎓 User100"}, BLACK: {"name": "🥷 Mario 🥷"}}}
    assert chess_game._player_label(game, WHITE) == f"{KING_GLYPHS[WHITE]} 🎓 User100"
    assert chess_game._player_label(game, BLACK) == f"{KING_GLYPHS[BLACK]} 🥷 Mario 🥷"


def _loc_with_you_are(code, tid):
    if tid.name == "MINI_GAMES_YOU_ARE_TEXT_ID":
        return "You are {player}"
    return tid.name


def test_each_player_is_told_which_side_they_are():
    with patch("module.commands.chess_game.get_locale", side_effect=_loc_with_you_are):
        u1, q1 = _pvp_query("chess_play", 100)
        q1.message.chat_id = 10
        chess_handler(u1, MagicMock())
        u2, q2 = _pvp_query("chess_play", 200)
        q2.message.chat_id = 20
        context = MagicMock()
        chess_handler(u2, context)
    first_lines = [
        call.kwargs["text"].splitlines()[0]
        for call in context.bot.editMessageText.call_args_list
    ]
    assert all(line.startswith("You are") for line in first_lines)
    assert any(KING_GLYPHS[WHITE] in line for line in first_lines)
    assert any(KING_GLYPHS[BLACK] in line for line in first_lines)


def test_names_block_shows_captured_pieces():
    game = {
        "white_captured": "pn",
        "black_captured": "",
        "players": {WHITE: {"name": "A"}, BLACK: {"name": "B"}},
    }
    with patch(
        "module.commands.chess_game.get_locale",
        side_effect=lambda loc, tid: "Catturati:",
    ):
        block = chess_game._names_block(game, "it")
    assert f"Catturati: {PIECE_GLYPHS['p']}{PIECE_GLYPHS['n']}" in block
