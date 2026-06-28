"""Tris (tic-tac-toe) vs CPU for the /minigames hub.

The full game state is encoded in the inline buttons' callback_data, so no per-user
state is kept server side. callback_data forms (all under the ``ttt_`` prefix):
    ttt_hub                       -> back to the mini games hub
    ttt_diff                      -> difficulty selection
    ttt_new_<d>                   -> fresh board at difficulty <d> in {e, m, h}
    ttt_mv_<d>_<s>_<board>_<cell> -> player plays <cell> on <board> (9 chars of -/x/o)

<s> in {x, o} is the symbol the human's marks are drawn as (picked at random per game);
it only changes the rendered glyphs, the internal player is always 'x' and moves first.
"""

import random
from typing import List, Optional, Tuple

from telegram import InlineKeyboardButton, Update
from telegram.ext import CallbackContext

from module.commands.minigames import _edit, _hub_keyboard
from module.data.vars import TEXT_IDS
from module.utils.multi_lang_utils import get_locale

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


def tictactoe_handler(update: Update, context: CallbackContext) -> None:
    """Called by every ttt_* callback. Routes between hub, difficulty and the board."""
    query = update.callback_query
    query.answer()
    locale: str = query.from_user.language_code
    data: str = query.data

    if data == "ttt_hub":
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.MINI_GAMES_HEADER_TEXT_ID),
            _hub_keyboard(locale),
        )
    elif data == "ttt_diff":
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.TRIS_SELECT_DIFFICULTY_TEXT_ID),
            _difficulty_keyboard(locale),
        )
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
        keyboard = (
            _board_keyboard(board, diff, player_symbol, False, _winning_line(board))
            + _replay_row(locale)
        )
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
