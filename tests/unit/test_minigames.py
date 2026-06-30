# -*- coding: utf-8 -*-
"""Test suite for the /minigames command (Tris)."""

# pylint: disable=protected-access,import-outside-toplevel,unused-variable,unused-argument,implicit-str-concat,chained-comparison

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from module.commands import tris
from module.commands.minigames import (
    DEFAULT_RATING,
    NINJA_ICON,
    _hub_keyboard,
    _leaderboard_name,
    _leaderboard_rows,
    _match_counts,
    _settings_keyboard,
    _stats_text,
    anonymous_display_name,
    apply_match_result,
    ensure_score,
    get_anonymous_name,
    get_rating,
    is_anonymous,
    is_ranked,
    log_match,
    minigames_input_name,
    minigames_settings_handler,
    minigames_stats,
    random_anonymous_name,
    set_anonymous,
    set_anonymous_name,
    set_ranked,
)
from module.commands.tris import (
    CPU,
    EMPTY,
    GLYPHS,
    PLAYER,
    STUDENT_ICONS,
    WIN_GLYPHS,
    _ai_move,
    _board_keyboard,
    _cpu_turn_text,
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


def test_cpu_turn_text_uses_the_actual_player_symbol():
    def loc(code, tid):
        if tid.name == "TRIS_YOUR_TURN_TEXT_ID":
            return "Your turn!"
        if tid.name == "MINI_GAMES_YOU_ARE_TEXT_ID":
            return "You are {player}"
        return tid.name

    with patch("module.commands.tris.get_locale", side_effect=loc), patch(
        "module.commands.minigames.get_locale", side_effect=loc
    ):
        assert _cpu_turn_text(CPU, "en") == f"Your turn!\nYou are {GLYPHS[CPU]}"


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


_PVP_TABLES = (
    "minigames_queue",
    "tris_game",
    "minigames_settings",
    "minigames_score",
    "minigames_match_log",
)


@pytest.fixture(autouse=True)
def _reset_pvp_state():
    for table in _PVP_TABLES:
        DbManager.delete_from(table)
    yield
    for table in _PVP_TABLES:
        DbManager.delete_from(table)


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


def test_ranked_match_updates_ratings_and_shows_change():
    set_ranked(100, True)
    set_ranked(200, True)
    game = _active_game()
    _set_board(game["id"], "xx-oo----")
    x_player_id = game["players"][PLAYER]["user_id"]
    _, context = _move(game, x_player_id, 2)  # completes the top row, wins
    texts = [c.kwargs["text"] for c in context.bot.editMessageText.call_args_list]
    assert all("Rating:" in t for t in texts)  # both players see their change
    winner_rating = get_rating(x_player_id)
    assert winner_rating > DEFAULT_RATING


def test_unranked_match_leaves_ratings_untouched():
    game = _active_game()  # both players unranked by default
    _set_board(game["id"], "xx-oo----")
    x_player_id = game["players"][PLAYER]["user_id"]
    _, context = _move(game, x_player_id, 2)
    texts = [c.kwargs["text"] for c in context.bot.editMessageText.call_args_list]
    assert not any("Rating:" in t for t in texts)
    assert get_rating(x_player_id) == DEFAULT_RATING


def test_finishing_pvp_match_is_logged():
    game = _active_game()
    _set_board(game["id"], "xx-oo----")
    x_player_id = game["players"][PLAYER]["user_id"]
    _move(game, x_player_id, 2)  # completes the top row
    assert sum(r["n"] for r in _match_counts()) == 1


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


# ---- settings (anonymity, shared across mini games)


def test_hub_keyboard_has_settings_button():
    with patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        keyboard = _hub_keyboard("it")
    assert any(btn.callback_data == "mg_settings" for row in keyboard for btn in row)


def test_hub_keyboard_has_ranking_button():
    with patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        keyboard = _hub_keyboard("it")
    assert any(btn.callback_data == "mg_ranking" for row in keyboard for btn in row)


# ---- ranked preference and MMR (shared score profile)


def test_player_is_unranked_by_default():
    assert is_ranked(100) is False


def test_set_ranked_persists_and_toggles():
    set_ranked(100, True)
    assert is_ranked(100) is True
    set_ranked(100, False)
    assert is_ranked(100) is False


def test_setting_ranked_does_not_disturb_anonymity():
    set_anonymous(100, False)
    set_anonymous_name(100, "Mario")
    set_ranked(100, True)
    assert is_anonymous(100) is False
    assert get_anonymous_name(100) == "Mario"
    assert is_ranked(100) is True


def test_settings_handler_ranked_toggle_persists():
    update, query = _make_query("mg_ranked")
    query.from_user.id = 100
    with patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        minigames_settings_handler(update, MagicMock())
    assert is_ranked(100) is True  # default off, toggled on


def test_default_rating_when_no_games_played():
    assert get_rating(100) == DEFAULT_RATING


def test_winner_gains_and_loser_loses_equal_points_from_even_rating():
    ensure_score(100, "A")
    ensure_score(200, "B")
    deltas = apply_match_result(winner_id=100, loser_id=200)
    win_rating, win_delta = deltas[100]
    lose_rating, lose_delta = deltas[200]
    assert win_delta > 0 and lose_delta < 0
    assert win_delta == -lose_delta  # symmetric at equal starting ratings
    assert get_rating(100) == win_rating
    assert get_rating(200) == lose_rating
    assert win_rating + lose_rating == 2 * DEFAULT_RATING  # zero-sum


def test_draw_barely_moves_equal_ratings():
    ensure_score(100, "A")
    ensure_score(200, "B")
    deltas = apply_match_result(100, 200, draw=True)
    assert deltas[100][1] == 0  # K*(0.5 - 0.5) rounds to 0 between equals
    assert deltas[200][1] == 0


def test_underdog_win_gains_more_than_favourite():
    ensure_score(100, "Favourite")
    ensure_score(200, "Underdog")
    apply_match_result(winner_id=100, loser_id=200)  # favourite pulls ahead
    assert get_rating(100) > get_rating(200)
    # underdog beating the now-higher favourite should swing more than an even game's 16
    deltas = apply_match_result(winner_id=200, loser_id=100)
    assert deltas[200][1] > 16


def test_leaderboard_lists_only_players_with_games_ordered_by_rating():
    ensure_score(100, "A")  # never finishes a ranked game
    ensure_score(200, "B")
    ensure_score(300, "C")
    apply_match_result(winner_id=200, loser_id=300)
    rows = _leaderboard_rows()
    listed = [r["user_id"] for r in rows]
    assert listed == [200, 300]  # 100 has no games; winner first
    assert 100 not in listed


def test_leaderboard_name_uses_real_name_when_public():
    set_anonymous(100, False)
    ensure_score(100, "Mario")
    row = {"user_id": 100, "first_name": "Mario", "public_id": 7}
    assert _leaderboard_name(row, "it") == "🎓 Mario"


def test_leaderboard_name_uses_custom_alias():
    set_anonymous_name(100, "Drago")  # anonymous by default, with a custom alias
    row = {"user_id": 100, "first_name": "Mario", "public_id": 7}
    assert _leaderboard_name(row, "it") == f"{NINJA_ICON} Drago {NINJA_ICON}"


def test_leaderboard_name_uses_public_id_when_fully_anonymous():
    row = {"user_id": 100, "first_name": "Mario", "public_id": 7}  # anon, no alias
    with patch(
        "module.commands.minigames.get_locale",
        side_effect=lambda loc, tid: "Player #{id}",
    ):
        assert _leaderboard_name(row, "it") == "Player #7"


# ---- match log and /minigames_stats


def test_log_match_counts_per_game():
    log_match("tris")
    log_match("tris")
    log_match("chess")
    assert {r["game"]: r["n"] for r in _match_counts()} == {"tris": 2, "chess": 1}


def test_recent_window_excludes_old_matches():
    log_match("tris")  # today
    old = str(date.today() - timedelta(days=60))
    DbManager.insert_into(
        "minigames_match_log", values=("tris", old), columns=("game", "finished_at")
    )
    assert {r["game"]: r["n"] for r in _match_counts()} == {"tris": 2}  # overall
    assert {r["game"]: r["n"] for r in _match_counts(days=30)} == {"tris": 1}  # recent


def test_stats_text_shows_recent_and_overall_counts():
    log_match("tris")
    log_match("chess")

    def loc(code, tid):
        return {
            "MINI_GAMES_STATS_HEADER_TEXT_ID": "HEAD",
            "MINI_GAMES_STATS_LAST_DAYS_TEXT_ID": "last {days}",
            "MINI_GAMES_STATS_OVERALL_TEXT_ID": "overall",
            "MINI_GAMES_STATS_TOTAL_TEXT_ID": "tot {total}",
            "MINI_GAMES_STATS_EMPTY_TEXT_ID": "empty",
        }.get(tid.name, tid.name)

    with patch("module.commands.minigames.get_locale", side_effect=loc):
        text = _stats_text("it")
    assert "last 30" in text and "overall" in text
    assert "Tris: 1" in text and "Chess: 1" in text
    assert text.count("tot 2") == 2  # same totals for recent and overall here


def test_stats_text_when_no_matches():
    def loc(code, tid):
        return "empty" if tid.name == "MINI_GAMES_STATS_EMPTY_TEXT_ID" else tid.name

    with patch("module.commands.minigames.get_locale", side_effect=loc):
        text = _stats_text("it")
    assert text.count("empty") == 2  # both sections report no matches


def test_minigames_stats_command_sends_message():
    log_match("tris")
    update = MagicMock()
    update.message.from_user.language_code = "it"
    update.message.chat_id = 5
    context = MagicMock()
    with patch("module.commands.minigames.check_log"), patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        minigames_stats(update, context)
    text = context.bot.sendMessage.call_args.kwargs["text"]
    assert "Tris: 1" in text


def test_finishing_cpu_game_is_logged():
    update, query = _make_query("ttt_mv_h_x_xx-oo----_2")  # completes the top row
    with patch(
        "module.commands.tris.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        tictactoe_handler(update, MagicMock())
    assert sum(r["n"] for r in _match_counts()) == 1


def test_player_is_anonymous_by_default():
    assert is_anonymous(100) is True


def test_set_anonymous_persists_and_toggles():
    set_anonymous(100, False)
    assert is_anonymous(100) is False
    set_anonymous(100, True)
    assert is_anonymous(100) is True


def test_random_anonymous_name_comes_from_file():
    from module.shared import read_md

    names = {n.strip() for n in read_md("anonymous_names").splitlines() if n.strip()}
    for _ in range(20):
        assert random_anonymous_name() in names


def test_settings_keyboard_reflects_state():
    with patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        on = _settings_keyboard("it", True, None, False)
        off = _settings_keyboard("it", False, None, False)
    assert on[0][0].callback_data == "mg_anon"
    assert on[0][0].text.endswith("✅")
    assert off[0][0].text.endswith("❌")


def test_settings_keyboard_reflects_ranked_state():
    with patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        on = _settings_keyboard("it", True, None, True)
        off = _settings_keyboard("it", True, None, False)
    assert on[1][0].callback_data == "mg_ranked"
    assert on[1][0].text.endswith("✅")
    assert off[1][0].text.endswith("❌")


def test_settings_keyboard_has_info_button():
    with patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        keyboard = _settings_keyboard("it", True, None, False)
    assert any(btn.callback_data == "mg_info" for row in keyboard for btn in row)


def test_info_handler_shows_profile_summary():
    set_anonymous(100, False)
    set_ranked(100, True)
    set_anonymous_name(100, "Drago")

    def loc(code, tid):
        if tid.name == "MINI_GAMES_INFO_BODY_TEXT_ID":
            return "anon={anonymous} ranked={ranked} name={name} rating={rating}"
        return tid.name

    update, query = _make_query("mg_info")
    query.from_user.id = 100
    context = MagicMock()
    with patch("module.commands.minigames.get_locale", side_effect=loc):
        minigames_settings_handler(update, context)
    text = context.bot.editMessageText.call_args.kwargs["text"]
    assert "anon=❌" in text  # set non-anonymous above
    assert "ranked=✅" in text
    assert "name=Drago" in text
    assert "rating=1000" in text  # default, no ranked games played yet


def test_info_handler_shows_dash_when_no_custom_name():
    def loc(code, tid):
        if tid.name == "MINI_GAMES_INFO_BODY_TEXT_ID":
            return "name={name}"
        return tid.name

    update, query = _make_query("mg_info")
    query.from_user.id = 100
    context = MagicMock()
    with patch("module.commands.minigames.get_locale", side_effect=loc):
        minigames_settings_handler(update, context)
    assert context.bot.editMessageText.call_args.kwargs["text"] == "name=—"


def test_settings_keyboard_shows_custom_name():
    with patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        keyboard = _settings_keyboard("it", True, "Mario", False)
    name_button = keyboard[2][0]
    assert name_button.callback_data == "mg_setname"
    assert name_button.text == f"{NINJA_ICON} Mario {NINJA_ICON}"


def test_settings_handler_toggle_persists_and_redraws():
    update, query = _make_query("mg_anon")
    query.from_user.id = 100
    context = MagicMock()
    with patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        minigames_settings_handler(update, context)
    # default was anonymous (True); the toggle flips it off and persists
    assert is_anonymous(100) is False
    context.bot.editMessageText.assert_called_once()


def test_anonymous_player_queues_under_alias():
    from module.shared import read_md

    aliases = {n.strip() for n in read_md("anonymous_names").splitlines() if n.strip()}
    _enqueue(100, chat_id=10)  # anonymous by default
    assert _queue()[0]["name"] in aliases


def test_non_anonymous_player_queues_under_real_name():
    set_anonymous(100, False)
    _enqueue(100, chat_id=10)
    assert _queue()[0]["name"] == f"{tris.PLAYER_ICON} User100"


def test_anonymous_player_with_custom_name_queues_wrapped_in_ninja():
    set_anonymous_name(100, "Mario")
    _enqueue(100, chat_id=10)  # anonymous by default
    assert _queue()[0]["name"] == f"{NINJA_ICON} Mario {NINJA_ICON}"


def test_each_player_is_told_their_mark_and_opponent():
    def loc(code, tid):
        if tid.name == "MINI_GAMES_YOU_ARE_TEXT_ID":
            return "You are {player}"
        if tid.name == "MINI_GAMES_OPPONENT_TEXT_ID":
            return "Opponent: {player}"
        return tid.name

    # you_are/opponent text comes from the minigames module, the turn line from tris
    with patch("module.commands.minigames.get_locale", side_effect=loc), patch(
        "module.commands.tris.get_locale", side_effect=loc
    ):
        u1, q1 = _pvp_query("ttt_pvp", 100)
        q1.message.chat_id = 10
        tictactoe_handler(u1, MagicMock())
        u2, q2 = _pvp_query("ttt_pvp", 200)
        q2.message.chat_id = 20
        context = MagicMock()
        tictactoe_handler(u2, context)
    texts = [call.kwargs["text"] for call in context.bot.editMessageText.call_args_list]
    # each player's message leads with their own side, then the opponent (shown once)
    for text in texts:
        lines = text.splitlines()
        assert lines[0].startswith("You are")
        assert lines[1].startswith("Opponent:")
    first_lines = [t.splitlines()[0] for t in texts]
    assert any(GLYPHS[PLAYER] in line for line in first_lines)
    assert any(GLYPHS[CPU] in line for line in first_lines)


def test_player_label_uses_stored_name_verbatim():
    game = {"players": {PLAYER: {"name": "🥷 Mario 🥷"}, CPU: {"name": "🎓 Luigi"}}}
    assert tris._player_label(game, PLAYER) == f"🥷 Mario 🥷 - {GLYPHS[PLAYER]}"
    assert tris._player_label(game, CPU) == f"🎓 Luigi - {GLYPHS[CPU]}"


# ---- custom anonymous name


def test_set_and_get_anonymous_name():
    assert get_anonymous_name(100) is None
    set_anonymous_name(100, "Mario")
    assert get_anonymous_name(100) == "Mario"


def test_set_anonymous_preserves_custom_name():
    set_anonymous_name(100, "Mario")
    set_anonymous(100, False)
    assert get_anonymous_name(100) == "Mario"
    assert is_anonymous(100) is False


def test_set_anonymous_name_preserves_anonymous_flag():
    set_anonymous(100, False)
    set_anonymous_name(100, "Mario")
    assert is_anonymous(100) is False


def test_anonymous_display_name_falls_back_to_random_alias():
    from module.shared import read_md

    aliases = {n.strip() for n in read_md("anonymous_names").splitlines() if n.strip()}
    assert anonymous_display_name(100) in aliases  # no custom name set


def _input_name(user_id, text):
    update, query = _make_query(text)
    update.message.text = text
    update.message.chat_id = 10
    update.message.from_user.id = user_id
    update.message.from_user.language_code = "it"
    context = MagicMock()
    context.user_data = {"minigames": {"awaiting_name": True}}
    with patch(
        "module.commands.minigames.get_locale", side_effect=lambda loc, tid: tid.name
    ):
        minigames_input_name(update, context)
    return context


def test_input_name_stores_valid_name():
    context = _input_name(100, "Nick: Mario Rossi")
    assert get_anonymous_name(100) == "Mario Rossi"
    context.bot.sendMessage.assert_called_once()


def test_input_name_rejects_at_sign():
    context = _input_name(100, "Nick: Mario@home")
    assert get_anonymous_name(100) is None  # nothing stored
    sent = context.bot.sendMessage.call_args.kwargs["text"]
    assert sent == "MINI_GAMES_NAME_INVALID_TEXT_ID"


def test_input_name_ignored_without_awaiting_flag():
    update, query = _make_query("Nick: Mario")
    update.message.text = "Nick: Mario"
    update.message.from_user.id = 100
    context = MagicMock()
    context.user_data = {"minigames": {}}
    minigames_input_name(update, context)
    assert get_anonymous_name(100) is None
    context.bot.sendMessage.assert_not_called()
