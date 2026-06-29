"""Chess for the /minigames hub, player vs player only.

A chess position can't fit in callback_data (the 64-byte limit), so every game is stored in
the database as a FEN string; the ``python-chess`` library handles all the rules (legal moves,
check/checkmate/stalemate, castling, en passant) and the captured pieces. Two players match
from their own private chats, exactly like tris vs-player: the shared ``minigames_queue``
(rows tagged ``game = 'chess'``) holds players waiting for an opponent, and ``chess_game``
holds the live games. White always moves first; whose turn it is comes from the FEN.

Moving takes two taps (pick a piece, then a destination). The first tap is rendered only on
the tapping player's own message and carries no server state: the destination buttons encode
the move in their callback_data, so nothing is persisted until the move is actually played.

callback_data forms (all under the ``chess_`` prefix):
    chess_play                       -> enter matchmaking (queue or pair up)
    chess_pcancel                    -> leave the matchmaking queue
    chess_sel_<gid>_<sq>             -> highlight square <sq>'s legal moves (own message only)
    chess_open_<gid>                 -> clear the selection (own message only)
    chess_mv_<gid>_<from>_<to>       -> play <from>-<to> in game <gid>
    chess_resign_<gid>               -> resign game <gid>

Pieces use the solid (filled) chess glyphs for both armies with a ○/● disc marking the side,
since Unicode has no "filled white" glyph and the outline ones render faint on dark themes.
Each player is labelled with their stored name (a 🎓-prefixed real name, or an anonymous alias
per the mini games settings) and their king glyph, and the pieces they have captured are shown
next to their name.
"""

import logging
import os
import random
import sqlite3
import time
from typing import List, Optional, Tuple

import chess
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext

from module.commands.minigames import (
    _edit,
    _hub_keyboard,
    anonymous_display_name,
    is_anonymous,
)
from module.data import DbManager
from module.data.vars import TEXT_IDS
from module.utils.multi_lang_utils import get_locale

logger = logging.getLogger(__name__)

WHITE, BLACK = 'w', 'b'
OTHER = {WHITE: BLACK, BLACK: WHITE}
# Unicode has no "filled white" chess glyph, so both armies use the solid (filled) shapes and
# a hollow/filled disc marks the side. The text-style ○/● (not the ⚪/⚫ emoji) render at text
# size, so the small disc stays subtle next to the piece while still telling the colours apart.
WHITE_DISC, BLACK_DISC = '○', '●'
_SOLID = {'K': '♚', 'Q': '♛', 'R': '♜', 'B': '♝', 'N': '♞', 'P': '♟'}
PIECE_GLYPHS = {
    **{sym: f"{WHITE_DISC}{glyph}" for sym, glyph in _SOLID.items()},
    **{sym.lower(): f"{BLACK_DISC}{glyph}" for sym, glyph in _SOLID.items()},
}
KING_GLYPHS = {WHITE: f"{WHITE_DISC}♚", BLACK: f"{BLACK_DISC}♚"}
EMPTY_SQUARE = '.'  # Telegram rejects blank button labels, so empty squares show a dot
MOVE_DOT = '🟢'  # empty square a selected piece may move to
CAPTURE_DOT = '🔴'  # enemy piece a selected piece may capture
PLAYER_ICON = '🎓'  # in-game label for a player using their real name

WAITING_TIMEOUT = 300  # seconds an entry may wait before the cleanup job reclaims it
GAME_CHESS = 'chess'  # value of the shared queue's ``game`` column for chess rows
QUEUE_TABLE = "minigames_queue"
GAME_TABLE = "chess_game"


def chess_handler(update: Update, context: CallbackContext) -> None:
    """Called by every chess_* callback. Routes between matchmaking, selection and moves."""
    query = update.callback_query
    locale: str = query.from_user.language_code
    data: str = query.data

    # these answer the callback themselves so they can raise alerts
    if data.startswith("chess_mv_"):
        _handle_pvp_move(context, query, locale, data)
        return
    if data.startswith("chess_resign_"):
        _handle_resign(context, query, locale, data)
        return
    if data.startswith("chess_sel_"):
        _handle_select(context, query, locale, data)
        return
    if data.startswith("chess_open_"):
        _handle_open(context, query, locale, data)
        return

    query.answer()
    if data == "chess_play":
        _start_pvp(context, query, locale)
    elif data == "chess_pcancel":
        _cancel_pvp(context, query, locale)


# ---- matchmaking (mirrors the tris vs-player queue; shared minigames_queue)


def _start_pvp(context: CallbackContext, query, locale: str) -> None:
    """Queue the player, or pair them with the player who has waited longest."""
    user = query.from_user
    if is_anonymous(user.id):
        name = anonymous_display_name(user.id)
    elif user.first_name:
        name = f"{PLAYER_ICON} {user.first_name}"
    else:
        name = PLAYER_ICON
    player = {
        'user_id': user.id,
        'chat_id': query.message.chat_id,
        'message_id': query.message.message_id,
        'name': name,
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
            (GAME_CHESS, player['user_id']),
        )
        cur.execute(
            f"SELECT * FROM {QUEUE_TABLE} "
            "WHERE game = ? AND queued_at >= ? ORDER BY queued_at LIMIT 1",
            (GAME_CHESS, cutoff),
        )
        opponent = cur.fetchone()
        cur.execute(
            f"SELECT user_id FROM {QUEUE_TABLE} WHERE game = ? ORDER BY queued_at",
            (GAME_CHESS,),
        )
        waiting = [r['user_id'] for r in cur.fetchall()]
        if opponent is None:
            cur.execute(
                f"INSERT INTO {QUEUE_TABLE} "
                "(game, user_id, chat_id, message_id, name, locale, queued_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    GAME_CHESS,
                    player['user_id'],
                    player['chat_id'],
                    player['message_id'],
                    player['name'],
                    player['locale'],
                    now,
                ),
            )
            logger.info(
                "chess[pid=%s] user %s queued; waiting=%s",
                os.getpid(),
                player['user_id'],
                waiting,
            )
        else:
            cur.execute(
                f"DELETE FROM {QUEUE_TABLE} WHERE game = ? AND user_id = ?",
                (GAME_CHESS, opponent['user_id']),
            )
            game_id = _insert_game(cur, opponent, player, now)
            logger.info(
                "chess[pid=%s] user %s paired with %s; waiting was %s",
                os.getpid(),
                player['user_id'],
                opponent['user_id'],
                waiting,
            )
        cur.execute("COMMIT")
    except sqlite3.Error as err:
        logger.error("chess _match_or_enqueue: %s", err)
        cur.execute("ROLLBACK")
        game_id = None
    finally:
        cur.close()
        conn.close()
    return _load_game(game_id) if game_id is not None else None


def _insert_game(cur: sqlite3.Cursor, a: dict, b: dict, now: float) -> int:
    """Insert a game between two players, randomizing who plays White (moves first)."""
    white, black = (a, b) if random.random() < 0.5 else (b, a)
    cur.execute(
        f"INSERT INTO {GAME_TABLE} "
        "(fen, white_captured, black_captured, last_san, "
        "w_user_id, w_chat_id, w_message_id, w_name, w_locale, "
        "b_user_id, b_chat_id, b_message_id, b_name, b_locale, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            chess.STARTING_FEN,
            '',
            '',
            None,
            white['user_id'],
            white['chat_id'],
            white['message_id'],
            white['name'],
            white['locale'],
            black['user_id'],
            black['chat_id'],
            black['message_id'],
            black['name'],
            black['locale'],
            now,
        ),
    )
    return cur.lastrowid


def _cancel_pvp(context: CallbackContext, query, locale: str) -> None:
    """Leave the matchmaking queue and return to the mini games hub."""
    DbManager.delete_from(
        QUEUE_TABLE,
        where="game = ? AND user_id = ?",
        where_args=(GAME_CHESS, query.from_user.id),
    )
    _edit(
        context,
        query,
        get_locale(locale, TEXT_IDS.MINI_GAMES_HEADER_TEXT_ID),
        _hub_keyboard(locale),
    )


# ---- loading / persistence


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
        'fen': row['fen'],
        'white_captured': row['white_captured'] or '',
        'black_captured': row['black_captured'] or '',
        'last_san': row['last_san'],
        'players': {
            WHITE: _row_to_player(row, WHITE),
            BLACK: _row_to_player(row, BLACK),
        },
    }


def _load_game(game_id: int) -> Optional[dict]:
    rows = DbManager.select_from(
        table_name=GAME_TABLE, where="game_id = ?", where_args=(game_id,)
    )
    return _row_to_game(rows[0]) if rows else None


# ---- moves


def _handle_pvp_move(context: CallbackContext, query, locale: str, data: str) -> None:
    """Validate the move against the stored game, then refresh both boards."""
    game_id_str, from_str, to_str = data[len("chess_mv_") :].split("_")
    game, status = _apply_pvp_move(
        int(game_id_str), query.from_user.id, int(from_str), int(to_str)
    )

    if status == 'not_in_game':
        query.answer(
            get_locale(locale, TEXT_IDS.CHESS_PVP_NOT_IN_GAME_TEXT_ID), show_alert=True
        )
        return
    if status == 'not_your_turn':
        query.answer(
            get_locale(locale, TEXT_IDS.CHESS_PVP_NOT_YOUR_TURN_TEXT_ID),
            show_alert=True,
        )
        return

    query.answer()
    if status == 'ok':
        _render_game(context, game)


def _apply_pvp_move(
    game_id: int, user_id: int, from_sq: int, to_sq: int
) -> Tuple[Optional[dict], str]:
    """Apply a move in a transaction. Returns (game to render, status).

    status is 'ok' (move applied), 'illegal' (stale button, nothing to redraw),
    'not_your_turn', or 'not_in_game' (unknown game or not a participant).
    """
    conn, cur = DbManager.get_db()
    conn.isolation_level = None
    new_state = None
    try:
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(f"SELECT * FROM {GAME_TABLE} WHERE game_id = ?", (game_id,))
        row = cur.fetchone()
        if row is None or user_id not in (row['w_user_id'], row['b_user_id']):
            cur.execute("ROLLBACK")
            return None, 'not_in_game'

        board = chess.Board(row['fen'])
        turn_mark = WHITE if board.turn == chess.WHITE else BLACK
        if row[f'{turn_mark}_user_id'] != user_id:
            cur.execute("ROLLBACK")
            return None, 'not_your_turn'

        move = _build_move(board, from_sq, to_sq)
        if move is None or move not in board.legal_moves:  # stale button
            cur.execute("ROLLBACK")
            return None, 'illegal'

        captured = _captured_symbol(board, move)
        san = board.san(move)
        board.push(move)

        white_captured = row['white_captured'] or ''
        black_captured = row['black_captured'] or ''
        if captured:
            if turn_mark == WHITE:
                white_captured += captured
            else:
                black_captured += captured

        new_fen = board.fen()
        if board.outcome() is None:  # game continues
            cur.execute(
                f"UPDATE {GAME_TABLE} SET fen = ?, white_captured = ?, "
                "black_captured = ?, last_san = ?, updated_at = ? WHERE game_id = ?",
                (new_fen, white_captured, black_captured, san, time.time(), game_id),
            )
        else:  # finished games are dropped, but still rendered one last time below
            cur.execute(f"DELETE FROM {GAME_TABLE} WHERE game_id = ?", (game_id,))
        cur.execute("COMMIT")
        new_state = (new_fen, white_captured, black_captured, san)
    except sqlite3.Error as err:
        logger.error("chess _apply_pvp_move: %s", err)
        cur.execute("ROLLBACK")
        return None, 'not_in_game'
    finally:
        cur.close()
        conn.close()

    game = _row_to_game(row)
    game['fen'], game['white_captured'], game['black_captured'], game['last_san'] = (
        new_state
    )
    return game, 'ok'


def _build_move(board: chess.Board, from_sq: int, to_sq: int) -> Optional[chess.Move]:
    """Build the move from/to, auto-queening a pawn that reaches the last rank."""
    piece = board.piece_at(from_sq)
    if piece is None:
        return None
    promotion = None
    if piece.piece_type == chess.PAWN and chess.square_rank(to_sq) in (0, 7):
        promotion = chess.QUEEN
    return chess.Move(from_sq, to_sq, promotion=promotion)


def _captured_symbol(board: chess.Board, move: chess.Move) -> Optional[str]:
    """The symbol of the piece this move captures (handling en passant), else None."""
    if not board.is_capture(move):
        return None
    if board.is_en_passant(move):
        # the captured pawn belongs to the side not to move
        return chess.Piece(chess.PAWN, not board.turn).symbol()
    victim = board.piece_at(move.to_square)
    return victim.symbol() if victim else None


# ---- resign


def _handle_resign(context: CallbackContext, query, locale: str, data: str) -> None:
    """End the game in favour of the opponent and refresh both boards."""
    game_id = int(data[len("chess_resign_") :])
    game, status, loser_mark = _apply_resign(game_id, query.from_user.id)
    if status == 'not_in_game':
        query.answer(
            get_locale(locale, TEXT_IDS.CHESS_PVP_NOT_IN_GAME_TEXT_ID), show_alert=True
        )
        return
    query.answer()
    _render_game(context, game, resigned_mark=loser_mark)


def _apply_resign(
    game_id: int, user_id: int
) -> Tuple[Optional[dict], str, Optional[str]]:
    """Drop the game in a transaction. Returns (game to render, status, loser mark)."""
    conn, cur = DbManager.get_db()
    conn.isolation_level = None
    try:
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(f"SELECT * FROM {GAME_TABLE} WHERE game_id = ?", (game_id,))
        row = cur.fetchone()
        if row is None or user_id not in (row['w_user_id'], row['b_user_id']):
            cur.execute("ROLLBACK")
            return None, 'not_in_game', None
        loser_mark = WHITE if row['w_user_id'] == user_id else BLACK
        cur.execute(f"DELETE FROM {GAME_TABLE} WHERE game_id = ?", (game_id,))
        cur.execute("COMMIT")
    except sqlite3.Error as err:
        logger.error("chess _apply_resign: %s", err)
        cur.execute("ROLLBACK")
        return None, 'not_in_game', None
    finally:
        cur.close()
        conn.close()
    return _row_to_game(row), 'ok', loser_mark


# ---- selection (own message only; the move is encoded in the buttons, not persisted)


def _handle_select(context: CallbackContext, query, locale: str, data: str) -> None:
    game_id_str, sq_str = data[len("chess_sel_") :].split("_")
    _render_selection(context, query, locale, int(game_id_str), int(sq_str))


def _handle_open(context: CallbackContext, query, locale: str, data: str) -> None:
    game_id = int(data[len("chess_open_") :])
    _render_selection(context, query, locale, game_id, None)


def _render_selection(
    context: CallbackContext, query, locale: str, game_id: int, selected: Optional[int]
) -> None:
    """Redraw only the tapping player's board, optionally highlighting a piece's moves."""
    game = _load_game(game_id)
    if game is None:
        query.answer(
            get_locale(locale, TEXT_IDS.CHESS_PVP_NOT_IN_GAME_TEXT_ID), show_alert=True
        )
        return
    board = chess.Board(game['fen'])
    turn_mark = WHITE if board.turn == chess.WHITE else BLACK
    if game['players'][turn_mark]['user_id'] != query.from_user.id:
        query.answer(
            get_locale(locale, TEXT_IDS.CHESS_PVP_NOT_YOUR_TURN_TEXT_ID),
            show_alert=True,
        )
        return
    if selected is not None:  # ignore a stale tap on a square without an own piece
        piece = board.piece_at(selected)
        if piece is None or _piece_mark(piece) != turn_mark:
            selected = None

    query.answer()
    text = f"{_you_are_text(game, turn_mark, locale)}\n\n{_turn_text(game, board, turn_mark, locale)}"
    keyboard = _board_keyboard(
        game, board, turn_mark, tappable=True, selected=selected
    ) + _controls_row(game['id'], locale)
    _edit(context, query, text, keyboard)


# ---- rendering


def _render_game(
    context: CallbackContext, game: dict, resigned_mark: Optional[str] = None
) -> None:
    """Edit both players' messages to reflect the current position."""
    board = chess.Board(game['fen'])
    result = _game_result(board, resigned_mark)
    turn_mark = WHITE if board.turn == chess.WHITE else BLACK
    for mark, player in game['players'].items():
        locale = player['locale']
        if result is None:
            text = _turn_text(game, board, turn_mark, locale)
            tappable = mark == turn_mark
            keyboard = _board_keyboard(
                game, board, mark, tappable=tappable, selected=None
            ) + _controls_row(game['id'], locale)
        else:
            text = _result_text(game, result, locale)
            keyboard = _board_keyboard(
                game, board, mark, tappable=False, selected=None
            ) + _replay_row(locale)
        text = f"{_you_are_text(game, mark, locale)}\n\n{text}"
        _deliver(context, game['id'], mark, player, text, keyboard)


def _game_result(
    board: chess.Board, resigned_mark: Optional[str]
) -> Optional[Tuple[str, Optional[str], Optional[str]]]:
    """Return (kind, winner mark, loser mark) for a finished game, else None.

    kind is 'checkmate', 'draw' or 'resign'.
    """
    if resigned_mark is not None:
        return 'resign', OTHER[resigned_mark], resigned_mark
    outcome = board.outcome()
    if outcome is None:
        return None
    if outcome.winner is None:
        return 'draw', None, None
    winner = WHITE if outcome.winner == chess.WHITE else BLACK
    return 'checkmate', winner, OTHER[winner]


def _piece_mark(piece: chess.Piece) -> str:
    return WHITE if piece.color == chess.WHITE else BLACK


def _display_squares(viewer_mark: str) -> List[List[int]]:
    """The 8x8 grid of square indices as the given player sees them (own side at the bottom)."""
    rows = []
    for dr in range(8):
        row = []
        for dc in range(8):
            if viewer_mark == WHITE:
                rank, file = 7 - dr, dc
            else:
                rank, file = dr, 7 - dc
            row.append(chess.square(file, rank))
        rows.append(row)
    return rows


def _board_keyboard(
    game: dict,
    board: chess.Board,
    viewer_mark: str,
    tappable: bool,
    selected: Optional[int],
) -> List[List[InlineKeyboardButton]]:
    """Render the 8x8 board from ``viewer_mark``'s perspective.

    When ``tappable`` and nothing is selected, the viewer's own pieces open a selection;
    when a piece is selected, its legal destinations become move buttons (🟢 empty, 🔴 capture)
    and the selected square itself clears the selection.
    """
    gid = game['id']
    turn_mark = WHITE if board.turn == chess.WHITE else BLACK
    targets = {}
    if selected is not None:
        for move in board.legal_moves:
            if move.from_square == selected:
                targets[move.to_square] = board.is_capture(move)

    rows = []
    for line in _display_squares(viewer_mark):
        row = []
        for sq in line:
            piece = board.piece_at(sq)
            if sq in targets:
                glyph = CAPTURE_DOT if targets[sq] else MOVE_DOT
                callback = f"chess_mv_{gid}_{selected}_{sq}"
            elif selected is not None and sq == selected:
                glyph = PIECE_GLYPHS[piece.symbol()]
                callback = f"chess_open_{gid}"
            elif piece is not None:
                glyph = PIECE_GLYPHS[piece.symbol()]
                if tappable and _piece_mark(piece) == turn_mark:
                    callback = f"chess_sel_{gid}_{sq}"
                else:
                    callback = "NONE"
            else:
                glyph = EMPTY_SQUARE
                callback = "NONE"
            row.append(InlineKeyboardButton(glyph, callback_data=callback))
        rows.append(row)
    return rows


def _render_captured(symbols: str) -> str:
    return ''.join(PIECE_GLYPHS[s] for s in symbols)


def _player_label(game: dict, mark: str) -> str:
    return f"{KING_GLYPHS[mark]} {game['players'][mark]['name']}"


def _you_are_text(game: dict, mark: str, locale: str) -> str:
    # both players can be anonymous aliases, so each message names which side is theirs
    return get_locale(locale, TEXT_IDS.MINI_GAMES_YOU_ARE_TEXT_ID).format(
        player=_player_label(game, mark)
    )


def _names_block(game: dict, locale: str) -> str:
    captured_label = get_locale(locale, TEXT_IDS.CHESS_PVP_CAPTURED_TEXT_ID)
    captured = {WHITE: game['white_captured'], BLACK: game['black_captured']}
    lines = []
    for mark in (WHITE, BLACK):
        line = _player_label(game, mark)
        taken = _render_captured(captured[mark])
        if taken:
            line += f"  {captured_label} {taken}"
        lines.append(line)
    return '\n'.join(lines)


def _last_move_line(game: dict, locale: str) -> Optional[str]:
    if not game['last_san']:
        return None
    return get_locale(locale, TEXT_IDS.CHESS_PVP_LAST_MOVE_TEXT_ID).format(
        move=game['last_san']
    )


def _turn_text(game: dict, board: chess.Board, turn_mark: str, locale: str) -> str:
    parts = [_names_block(game, locale), ""]
    last = _last_move_line(game, locale)
    if last:
        parts.append(last)
    if board.is_check():
        parts.append(get_locale(locale, TEXT_IDS.CHESS_PVP_CHECK_TEXT_ID))
    parts.append(
        get_locale(locale, TEXT_IDS.CHESS_PVP_TURN_TEXT_ID).format(
            player=_player_label(game, turn_mark)
        )
    )
    return '\n'.join(parts)


def _result_text(
    game: dict, result: Tuple[str, Optional[str], Optional[str]], locale: str
) -> str:
    kind, winner, loser = result
    parts = [_names_block(game, locale), ""]
    last = _last_move_line(game, locale)
    if last:
        parts.append(last)
    if kind == 'draw':
        parts.append(get_locale(locale, TEXT_IDS.CHESS_PVP_DRAW_TEXT_ID))
    else:
        if kind == 'resign':
            parts.append(
                get_locale(locale, TEXT_IDS.CHESS_PVP_RESIGNED_TEXT_ID).format(
                    player=_player_label(game, loser)
                )
            )
        parts.append(
            get_locale(locale, TEXT_IDS.CHESS_PVP_WIN_TEXT_ID).format(
                player=_player_label(game, winner)
            )
        )
    return '\n'.join(parts)


def _controls_row(game_id: str, locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CHESS_PVP_RESIGN_TEXT_ID),
                callback_data=f"chess_resign_{game_id}",
            )
        ]
    ]


def _waiting_text(locale: str) -> str:
    return get_locale(locale, TEXT_IDS.CHESS_PVP_WAITING_TEXT_ID)


def _waiting_keyboard(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CHESS_PVP_CANCEL_TEXT_ID),
                callback_data="chess_pcancel",
            )
        ]
    ]


def _replay_row(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CHESS_PLAY_AGAIN_TEXT_ID),
                callback_data="chess_play",
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

    Editing the player's message can fail (it was deleted, is past the 48h edit window, or a
    transient network error). When it does, send a fresh message and repoint the stored game
    at it so the next move still reaches them, instead of leaving them on a stale board.
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
    """Point the stored game's W/B message at a freshly sent one (no-op if game is over)."""
    conn, cur = DbManager.get_db()
    try:
        cur.execute(
            f"UPDATE {GAME_TABLE} SET {mark}_message_id = ? WHERE game_id = ?",
            (message_id, int(game_id)),
        )
        conn.commit()
    except sqlite3.Error as err:
        logger.error("chess _persist_message_id: %s", err)
    finally:
        cur.close()
        conn.close()


def expire_chess_waiters(context: CallbackContext) -> None:
    """JobQueue task: drop players who have waited too long and tell them to retry."""
    cutoff = time.time() - WAITING_TIMEOUT
    stale = DbManager.select_from(
        table_name=QUEUE_TABLE,
        where="game = ? AND queued_at < ?",
        where_args=(GAME_CHESS, cutoff),
    )
    if not stale:
        return
    DbManager.delete_from(
        QUEUE_TABLE, where="game = ? AND queued_at < ?", where_args=(GAME_CHESS, cutoff)
    )
    for row in stale:
        locale = row['locale']
        _safe_notify(
            context,
            row['chat_id'],
            row['message_id'],
            get_locale(locale, TEXT_IDS.CHESS_PVP_TIMEOUT_TEXT_ID),
            _replay_row(locale),
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
