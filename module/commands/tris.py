"""Tris (tic-tac-toe) for the /minigames hub, vs CPU or vs another player.

The vs-CPU game encodes its full state in the inline buttons' callback_data, so it keeps
nothing server side; vs-player is the exception (see the matchmaking section). callback_data
forms (all under the ``ttt_`` prefix):
    ttt_hub                          -> back to the mini games hub
    ttt_mode                         -> mode selection (vs CPU / vs player)
    ttt_diff                         -> difficulty selection (vs CPU)
    ttt_new_<d>                      -> fresh board at difficulty <d> in {e, m, h}
    ttt_mv_<d>_<s>_<board>_<cell>    -> player plays <cell> on <board> (9 chars of -/x/o)
    ttt_pvp                          -> enter online matchmaking (queue or pair up)
    ttt_pcancel                      -> leave the matchmaking queue
    ttt_pmv_<gid>_<cell>             -> play <cell> in live vs-player game <gid>

vs CPU: <s> in {x, o} is the symbol the human's marks are drawn as (picked at random per
game); it only changes the rendered glyphs, the internal player is always 'x' and moves
first. vs player pairs two users from their own private chats; that game state can't fit
in callback_data so it is stored in the database (see the matchmaking section below). Marks
stay ❌/⭕, each player is labelled with the 🎓 glyph, and the "vs player" menu button shows a
random graduate icon.
"""

import logging
import os
import random
import sqlite3
import time
from typing import List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext

from module.commands.minigames import _edit, _hub_keyboard
from module.data import DbManager
from module.data.vars import TEXT_IDS
from module.utils.multi_lang_utils import get_locale

logger = logging.getLogger(__name__)

PLAYER = 'x'
CPU = 'o'
EMPTY = '-'
GLYPHS = {PLAYER: '❌', CPU: '⭕', EMPTY: '▫️'}
WIN_GLYPHS = {PLAYER: '❎', CPU: '🟢'}  # green variants for the winning line
WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),  # rows
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),  # columns
    (0, 4, 8),
    (2, 4, 6),  # diagonals
)
DIFF_EASY, DIFF_MEDIUM, DIFF_HARD = 'e', 'm', 'h'
STUDENT_ICONS = ('👨‍🎓', '👩‍🎓')  # menu "vs player" button, random per render
PLAYER_ICON = '🎓'  # in-game label for both human players


def tictactoe_handler(update: Update, context: CallbackContext) -> None:
    """Called by every ttt_* callback. Routes between hub, difficulty and the board."""
    query = update.callback_query
    locale: str = query.from_user.language_code
    data: str = query.data

    # vs-player moves answer the callback themselves so they can raise alerts
    if data.startswith("ttt_pmv_"):
        _handle_pvp_move(context, query, locale, data)
        return

    query.answer()
    if data == "ttt_hub":
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.MINI_GAMES_HEADER_TEXT_ID),
            _hub_keyboard(locale),
        )
    elif data == "ttt_mode":
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.TRIS_SELECT_MODE_TEXT_ID),
            _mode_keyboard(locale),
        )
    elif data == "ttt_diff":
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.TRIS_SELECT_DIFFICULTY_TEXT_ID),
            _difficulty_keyboard(locale),
        )
    elif data == "ttt_pvp":
        _start_pvp(context, query, locale)
    elif data == "ttt_pcancel":
        _cancel_pvp(context, query, locale)
    elif data.startswith("ttt_new_"):
        diff = data[len("ttt_new_") :]
        player_symbol = random.choice((PLAYER, CPU))
        board = [EMPTY] * 9
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.TRIS_YOUR_TURN_TEXT_ID),
            _board_keyboard(board, diff, player_symbol, True),
        )
    elif data.startswith("ttt_mv_"):
        _handle_move(context, query, locale, data)


def _handle_move(context: CallbackContext, query, locale: str, data: str) -> None:
    """Apply the player's move, let the CPU respond and render the result."""
    diff, player_symbol, board_str, cell_str = data[len("ttt_mv_") :].split("_")
    board = list(board_str)
    cell = int(cell_str)
    if board[cell] != EMPTY:  # stale button, cell already taken
        return

    board[cell] = PLAYER
    end_text = _end_text(board, locale)
    if end_text is None:
        board[_ai_move(board, diff)] = CPU
        end_text = _end_text(board, locale)

    if end_text is not None:
        keyboard = _board_keyboard(
            board, diff, player_symbol, False, _winning_line(board)
        ) + _replay_row(locale)
        _edit(context, query, end_text, keyboard)
    else:
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.TRIS_YOUR_TURN_TEXT_ID),
            _board_keyboard(board, diff, player_symbol, True),
        )


def _end_text(board: List[str], locale: str) -> Optional[str]:
    """Return the localized end-of-game message, or None if the game continues."""
    winner = _winner(board)
    if winner == PLAYER:
        return get_locale(locale, TEXT_IDS.TRIS_WIN_TEXT_ID)
    if winner == CPU:
        return get_locale(locale, TEXT_IDS.TRIS_LOSE_TEXT_ID)
    if EMPTY not in board:
        return get_locale(locale, TEXT_IDS.TRIS_DRAW_TEXT_ID)
    return None


def _winning_line(board: List[str]) -> Optional[Tuple[int, int, int]]:
    """Return the indices of a complete line, else None."""
    for line in WIN_LINES:
        a, b, c = line
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return line
    return None


def _winner(board: List[str]) -> Optional[str]:
    """Return 'x' or 'o' if a line is complete, else None."""
    line = _winning_line(board)
    return board[line[0]] if line else None


def _ai_move(board: List[str], diff: str) -> int:
    """Pick the CPU's cell for the given difficulty."""
    empty = [i for i, cell in enumerate(board) if cell == EMPTY]
    if diff == DIFF_EASY:
        return random.choice(empty)
    if diff == DIFF_MEDIUM:
        return _medium_move(board, empty)
    move = _minimax(list(board), CPU)[1]
    return move if move is not None else random.choice(empty)


def _medium_move(board: List[str], empty: List[int]) -> int:
    """Win if possible, otherwise block the player, otherwise prefer center/corners."""
    for symbol in (CPU, PLAYER):  # take the win first, then block the player's win
        for i in empty:
            board[i] = symbol
            won = _winner(board) == symbol
            board[i] = EMPTY
            if won:
                return i
    if 4 in empty:
        return 4
    corners = [i for i in (0, 2, 6, 8) if i in empty]
    return random.choice(corners) if corners else random.choice(empty)


def _minimax(board: List[str], player: str) -> Tuple[int, Optional[int]]:
    """Exhaustive search; returns (score from the CPU's view, best move)."""
    winner = _winner(board)
    if winner == CPU:
        return 1, None
    if winner == PLAYER:
        return -1, None
    empty = [i for i, cell in enumerate(board) if cell == EMPTY]
    if not empty:
        return 0, None

    best_move = empty[0]
    best_score = -2 if player == CPU else 2
    nxt = PLAYER if player == CPU else CPU
    for i in empty:
        board[i] = player
        score, _ = _minimax(board, nxt)
        board[i] = EMPTY
        if (player == CPU and score > best_score) or (
            player == PLAYER and score < best_score
        ):
            best_score, best_move = score, i
    return best_score, best_move


def _mode_keyboard(locale: str) -> List[List[InlineKeyboardButton]]:
    pvp_label = (
        f"{random.choice(STUDENT_ICONS)}"
        f"{get_locale(locale, TEXT_IDS.TRIS_MODE_VS_PLAYER_TEXT_ID)}"
        f"{random.choice(STUDENT_ICONS)}"
    )
    return [
        [
            InlineKeyboardButton(
                f"{random.choice(STUDENT_ICONS)}"
                + get_locale(locale, TEXT_IDS.TRIS_MODE_VS_CPU_TEXT_ID),
                callback_data="ttt_diff",
            )
        ],
        [InlineKeyboardButton(pvp_label, callback_data="ttt_pvp")],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CLOSE_KEYBOARD_TEXT_ID),
                callback_data="exit_cmd",
            )
        ],
    ]


def _difficulty_keyboard(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.TRIS_DIFF_EASY_TEXT_ID),
                callback_data="ttt_new_e",
            ),
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.TRIS_DIFF_MEDIUM_TEXT_ID),
                callback_data="ttt_new_m",
            ),
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.TRIS_DIFF_HARD_TEXT_ID),
                callback_data="ttt_new_h",
            ),
        ],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CLOSE_KEYBOARD_TEXT_ID),
                callback_data="exit_cmd",
            )
        ],
    ]


def _display_shape(cell: str, player_symbol: str) -> str:
    """Map an internal cell value to the symbol it is drawn as for this game.

    The human (internal 'x') is shown as ``player_symbol``; the CPU gets the other one.
    """
    if cell == EMPTY:
        return EMPTY
    if cell == PLAYER:
        return player_symbol
    return CPU if player_symbol == PLAYER else PLAYER


def _board_keyboard(
    board: List[str],
    diff: str,
    player_symbol: str,
    playable: bool,
    win_line: Optional[Tuple[int, int, int]] = None,
) -> List[List[InlineKeyboardButton]]:
    board_str = ''.join(board)
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            shape = _display_shape(board[i], player_symbol)
            if win_line is not None and i in win_line:
                glyph = WIN_GLYPHS[shape]
            else:
                glyph = GLYPHS[shape]
            if playable and board[i] == EMPTY:
                callback = f"ttt_mv_{diff}_{player_symbol}_{board_str}_{i}"
            else:
                callback = "NONE"
            row.append(InlineKeyboardButton(glyph, callback_data=callback))
        rows.append(row)
    return rows


def _replay_row(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.TRIS_PLAY_AGAIN_TEXT_ID),
                callback_data="ttt_diff",
            ),
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CLOSE_KEYBOARD_TEXT_ID),
                callback_data="exit_cmd",
            ),
        ]
    ]


# ---- vs player (online matchmaking, persisted in the DB)
#
# Two players match from their own private chats, so the state can't live in callback_data
# like the vs-CPU game does. ``minigames_queue`` is shared by every mini game (each row tagged
# with a ``game`` identifier) and holds players waiting for an opponent, one row per (game,
# user). ``tris_game`` is tris-specific and holds live games (the board as 9 chars of -/x/o
# plus both players). X always moves first; whose turn it is is derived from the board. Pairing
# and moves run in an IMMEDIATE transaction so two updates can't grab the same opponent or play
# the same cell at once. Abandoned queue entries are reclaimed by :func:`expire_tris_waiters`.

WAITING_TIMEOUT = 300  # seconds an entry may wait before the cleanup job reclaims it
GAME_TRIS = 'tris'  # value of the shared queue's ``game`` column for tris rows
QUEUE_TABLE = "minigames_queue"
GAME_TABLE = "tris_game"


def _start_pvp(context: CallbackContext, query, locale: str) -> None:
    """Queue the player, or pair them with the player who has waited longest."""
    user = query.from_user
    player = {
        'user_id': user.id,
        'chat_id': query.message.chat_id,
        'message_id': query.message.message_id,
        'name': user.first_name or PLAYER_ICON,
        'locale': locale,
    }
    game = _match_or_enqueue(player)
    if game is None:
        _edit(context, query, _waiting_text(locale), _waiting_keyboard(locale))
    else:
        _render_game(context, game)


def _match_or_enqueue(player: dict) -> Optional[dict]:
    """Pair with the oldest still-valid waiter, or enqueue. Returns the new game or None."""
    now = time.time()
    cutoff = now - WAITING_TIMEOUT
    conn, cur = DbManager.get_db()
    conn.isolation_level = None  # take explicit control of the transaction
    game_id = None
    try:
        cur.execute("BEGIN IMMEDIATE")
        # a re-click refreshes our own slot; stale rows are left for the cleanup job to notify
        cur.execute(
            f"DELETE FROM {QUEUE_TABLE} WHERE game = ? AND user_id = ?",
            (GAME_TRIS, player['user_id']),
        )
        cur.execute(
            f"SELECT * FROM {QUEUE_TABLE} "
            "WHERE game = ? AND queued_at >= ? ORDER BY queued_at LIMIT 1",
            (GAME_TRIS, cutoff),
        )
        opponent = cur.fetchone()
        cur.execute(
            f"SELECT user_id FROM {QUEUE_TABLE} WHERE game = ? ORDER BY queued_at",
            (GAME_TRIS,),
        )
        waiting = [r['user_id'] for r in cur.fetchall()]
        if opponent is None:
            cur.execute(
                f"INSERT INTO {QUEUE_TABLE} "
                "(game, user_id, chat_id, message_id, name, locale, queued_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    GAME_TRIS,
                    player['user_id'],
                    player['chat_id'],
                    player['message_id'],
                    player['name'],
                    player['locale'],
                    now,
                ),
            )
            logger.info(
                "tris[pid=%s] user %s queued; waiting=%s",
                os.getpid(),
                player['user_id'],
                waiting,
            )
        else:
            cur.execute(
                f"DELETE FROM {QUEUE_TABLE} WHERE game = ? AND user_id = ?",
                (GAME_TRIS, opponent['user_id']),
            )
            game_id = _insert_game(cur, opponent, player, now)
            logger.info(
                "tris[pid=%s] user %s paired with %s; waiting was %s",
                os.getpid(),
                player['user_id'],
                opponent['user_id'],
                waiting,
            )
        cur.execute("COMMIT")
    except sqlite3.Error as err:
        logger.error("tris _match_or_enqueue: %s", err)
        cur.execute("ROLLBACK")
        game_id = None
    finally:
        cur.close()
        conn.close()
    return _load_game(game_id) if game_id is not None else None


def _insert_game(cur: sqlite3.Cursor, a: dict, b: dict, now: float) -> int:
    """Insert a game between two players, randomizing who is X (moves first)."""
    first, second = (a, b) if random.random() < 0.5 else (b, a)
    cur.execute(
        f"INSERT INTO {GAME_TABLE} "
        "(board, x_user_id, x_chat_id, x_message_id, x_name, x_locale, "
        "o_user_id, o_chat_id, o_message_id, o_name, o_locale, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            EMPTY * 9,
            first['user_id'],
            first['chat_id'],
            first['message_id'],
            first['name'],
            first['locale'],
            second['user_id'],
            second['chat_id'],
            second['message_id'],
            second['name'],
            second['locale'],
            now,
        ),
    )
    return cur.lastrowid


def _row_to_player(row: dict, mark: str) -> dict:
    return {
        'user_id': row[f'{mark}_user_id'],
        'chat_id': row[f'{mark}_chat_id'],
        'message_id': row[f'{mark}_message_id'],
        'name': row[f'{mark}_name'],
        'locale': row[f'{mark}_locale'],
    }


def _row_to_game(row: dict) -> dict:
    return {
        'id': str(row['game_id']),
        'board': list(row['board']),
        'players': {PLAYER: _row_to_player(row, PLAYER), CPU: _row_to_player(row, CPU)},
    }


def _load_game(game_id: int) -> Optional[dict]:
    rows = DbManager.select_from(
        table_name=GAME_TABLE, where="game_id = ?", where_args=(game_id,)
    )
    return _row_to_game(rows[0]) if rows else None


def _cancel_pvp(context: CallbackContext, query, locale: str) -> None:
    """Leave the matchmaking queue and return to the mode menu."""
    DbManager.delete_from(
        QUEUE_TABLE,
        where="game = ? AND user_id = ?",
        where_args=(GAME_TRIS, query.from_user.id),
    )
    _edit(
        context,
        query,
        get_locale(locale, TEXT_IDS.TRIS_SELECT_MODE_TEXT_ID),
        _mode_keyboard(locale),
    )


def _handle_pvp_move(context: CallbackContext, query, locale: str, data: str) -> None:
    """Validate the move against the stored game, then refresh both boards."""
    game_id_str, cell_str = data[len("ttt_pmv_") :].split("_")
    game, status = _apply_pvp_move(int(game_id_str), query.from_user.id, int(cell_str))

    if status == 'not_in_game':
        query.answer(
            get_locale(locale, TEXT_IDS.TRIS_PVP_NOT_IN_GAME_TEXT_ID), show_alert=True
        )
        return
    if status == 'not_your_turn':
        query.answer(
            get_locale(locale, TEXT_IDS.TRIS_PVP_NOT_YOUR_TURN_TEXT_ID), show_alert=True
        )
        return

    query.answer()
    if status == 'ok':
        _render_game(context, game)


def _apply_pvp_move(
    game_id: int, user_id: int, cell: int
) -> Tuple[Optional[dict], str]:
    """Apply a move in a transaction. Returns (game to render, status).

    status is 'ok' (move applied), 'taken' (cell already used, nothing to redraw),
    'not_your_turn', or 'not_in_game' (unknown game or not a participant).
    """
    conn, cur = DbManager.get_db()
    conn.isolation_level = None
    try:
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(f"SELECT * FROM {GAME_TABLE} WHERE game_id = ?", (game_id,))
        row = cur.fetchone()
        if row is None or user_id not in (row['x_user_id'], row['o_user_id']):
            cur.execute("ROLLBACK")
            return None, 'not_in_game'

        board = list(row['board'])
        current_mark = PLAYER if board.count(PLAYER) == board.count(CPU) else CPU
        if row[f'{current_mark}_user_id'] != user_id:
            cur.execute("ROLLBACK")
            return None, 'not_your_turn'
        if board[cell] != EMPTY:  # stale button, cell already taken
            cur.execute("ROLLBACK")
            return None, 'taken'

        board[cell] = current_mark
        if _pvp_outcome(board) is None:
            cur.execute(
                f"UPDATE {GAME_TABLE} SET board = ?, updated_at = ? WHERE game_id = ?",
                (''.join(board), time.time(), game_id),
            )
        else:  # finished games are dropped, but still rendered one last time below
            cur.execute(f"DELETE FROM {GAME_TABLE} WHERE game_id = ?", (game_id,))
        cur.execute("COMMIT")
    except sqlite3.Error as err:
        logger.error("tris _apply_pvp_move: %s", err)
        cur.execute("ROLLBACK")
        return None, 'not_in_game'
    finally:
        cur.close()
        conn.close()

    game = _row_to_game(row)
    game['board'] = board
    return game, 'ok'


def _render_game(context: CallbackContext, game: dict) -> None:
    """Edit both players' messages to reflect the current board state."""
    board = game['board']
    outcome = _pvp_outcome(board)
    current_mark = PLAYER if board.count(PLAYER) == board.count(CPU) else CPU
    win_line = _winning_line(board)
    for mark, player in game['players'].items():
        locale = player['locale']
        if outcome is None:
            text = _pvp_turn_text(game, current_mark, locale)
            tappable = mark == current_mark
        else:
            text = _pvp_result_text(game, outcome, locale)
            tappable = False
        keyboard = _pvp_board_keyboard(game, tappable, win_line)
        if outcome is not None:
            keyboard = keyboard + _pvp_replay_row(locale)
        _deliver(context, game['id'], mark, player, text, keyboard)


def _pvp_outcome(board: List[str]) -> Optional[str]:
    """'x'/'o' for a winner, 'draw' for a full board, else None."""
    winner = _winner(board)
    if winner is not None:
        return winner
    if EMPTY not in board:
        return 'draw'
    return None


def _player_label(game: dict, mark: str) -> str:
    return f"{PLAYER_ICON} {game['players'][mark]['name']} {GLYPHS[mark]}"


def _pvp_names_block(game: dict) -> str:
    return f"{_player_label(game, PLAYER)}\n{_player_label(game, CPU)}"


def _pvp_turn_text(game: dict, current_mark: str, locale: str) -> str:
    turn = get_locale(locale, TEXT_IDS.TRIS_PVP_TURN_TEXT_ID).format(
        player=_player_label(game, current_mark)
    )
    return f"{_pvp_names_block(game)}\n\n{turn}"


def _pvp_result_text(game: dict, outcome: str, locale: str) -> str:
    if outcome == 'draw':
        result = get_locale(locale, TEXT_IDS.TRIS_DRAW_TEXT_ID)
    else:
        result = get_locale(locale, TEXT_IDS.TRIS_PVP_WIN_TEXT_ID).format(
            player=_player_label(game, outcome)
        )
    return f"{_pvp_names_block(game)}\n\n{result}"


def _pvp_board_keyboard(
    game: dict, tappable: bool, win_line: Optional[Tuple[int, int, int]]
) -> List[List[InlineKeyboardButton]]:
    board = game['board']
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            cell = board[i]
            if win_line is not None and i in win_line:
                glyph = WIN_GLYPHS[cell]
            else:
                glyph = GLYPHS[cell]
            if tappable and cell == EMPTY:
                callback = f"ttt_pmv_{game['id']}_{i}"
            else:
                callback = "NONE"
            row.append(InlineKeyboardButton(glyph, callback_data=callback))
        rows.append(row)
    return rows


def _waiting_text(locale: str) -> str:
    return get_locale(locale, TEXT_IDS.TRIS_PVP_WAITING_TEXT_ID)


def _waiting_keyboard(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.TRIS_PVP_CANCEL_TEXT_ID),
                callback_data="ttt_pcancel",
            )
        ]
    ]


def _pvp_replay_row(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.TRIS_PLAY_AGAIN_TEXT_ID),
                callback_data="ttt_pvp",
            ),
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CLOSE_KEYBOARD_TEXT_ID),
                callback_data="exit_cmd",
            ),
        ]
    ]


def _deliver(
    context: CallbackContext,
    game_id: str,
    mark: str,
    player: dict,
    text: str,
    keyboard: List[List[InlineKeyboardButton]],
) -> None:
    """Show ``text`` to ``player``, surviving an unusable old message.

    Editing the player's message can fail (it was deleted, is too old, or a transient
    network error). When it does, send a fresh message and repoint the stored game at it so
    the next move still reaches them, instead of leaving them stuck on a stale board.
    """
    markup = InlineKeyboardMarkup(keyboard)
    try:
        context.bot.editMessageText(
            text=text,
            chat_id=player['chat_id'],
            message_id=player['message_id'],
            reply_markup=markup,
        )
        return
    except TelegramError as err:
        if 'not modified' in str(err).lower():  # already showing this exact state
            return
    try:
        sent = context.bot.sendMessage(
            chat_id=player['chat_id'], text=text, reply_markup=markup
        )
    except TelegramError:
        return
    player['message_id'] = sent.message_id
    _persist_message_id(game_id, mark, sent.message_id)


def _persist_message_id(game_id: str, mark: str, message_id: int) -> None:
    """Point the stored game's X/O message at a freshly sent one (no-op if game is over)."""
    conn, cur = DbManager.get_db()
    try:
        cur.execute(
            f"UPDATE {GAME_TABLE} SET {mark}_message_id = ? WHERE game_id = ?",
            (message_id, int(game_id)),
        )
        conn.commit()
    except sqlite3.Error as err:
        logger.error("tris _persist_message_id: %s", err)
    finally:
        cur.close()
        conn.close()


def expire_tris_waiters(context: CallbackContext) -> None:
    """JobQueue task: drop players who have waited too long and tell them to retry."""
    cutoff = time.time() - WAITING_TIMEOUT
    stale = DbManager.select_from(
        table_name=QUEUE_TABLE,
        where="game = ? AND queued_at < ?",
        where_args=(GAME_TRIS, cutoff),
    )
    if not stale:
        return
    DbManager.delete_from(
        QUEUE_TABLE, where="game = ? AND queued_at < ?", where_args=(GAME_TRIS, cutoff)
    )
    for row in stale:
        locale = row['locale']
        _safe_notify(
            context,
            row['chat_id'],
            row['message_id'],
            get_locale(locale, TEXT_IDS.TRIS_PVP_TIMEOUT_TEXT_ID),
            _mode_keyboard(locale),
        )


def _safe_notify(
    context: CallbackContext,
    chat_id: int,
    message_id: int,
    text: str,
    keyboard: List[List[InlineKeyboardButton]],
) -> None:
    """Edit a message, ignoring failures (the player may have closed it)."""
    try:
        context.bot.editMessageText(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except TelegramError:
        pass
