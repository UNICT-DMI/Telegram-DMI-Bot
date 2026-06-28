# -*- coding: utf-8 -*-
"""Test suite for the /minigames command (Tris)."""

from unittest.mock import MagicMock, patch

from module.commands.tris import (
    CPU,
    EMPTY,
    GLYPHS,
    PLAYER,
    WIN_GLYPHS,
    _ai_move,
    _board_keyboard,
    _minimax,
    _winner,
    _winning_line,
    tictactoe_handler,
)

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
    with patch(
        "module.commands.tris.get_locale", return_value="win"
    ) as mock_locale:
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
