"""/minigames command — the mini games hub.

Holds the hub itself and the helpers shared across mini games. Each individual game
(e.g. Tris) lives in its own module and plugs into the hub from there.

Settings (under the ``mg_`` callback prefix) are shared by every game and stored per user
in ``minigames_settings``: whether the player is anonymous (on by default) and an optional
custom alias. An anonymous player is shown to opponents under a random alias, or under their
custom alias wrapped in 🥷 when they set one.

A second per-user table, ``minigames_score``, holds the shared score profile: an Elo-style
``rating`` (everyone starts at 1000), win/loss/draw counters, the ranked-match preference, and
a ``public_id`` shown on the leaderboard for players who stay fully anonymous (so the chat id is
never exposed). A match counts as ranked only when both players have ranked enabled; the rating
helpers here are called by each game when a ranked match ends.
"""

import logging
import re
import sqlite3
from random import choice
from typing import Dict, List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from module.data import DbManager
from module.data.vars import TEXT_IDS
from module.shared import check_log, read_md
from module.utils.multi_lang_utils import get_locale

logger = logging.getLogger(__name__)

SETTINGS_TABLE = "minigames_settings"
SCORE_TABLE = "minigames_score"
NINJA_ICON = "🥷"  # wraps a custom anonymous alias
GRADUATE_ICON = "🎓"  # prefixes a non-anonymous player's real name
MAX_ANON_NAME_LEN = 30
NAME_INPUT_PREFIX = r"^(?!=<[/])[Nn]ick:\s+"  # how the custom alias is typed in
DEFAULT_RATING = 1000  # everyone starts here
K_FACTOR = 32  # Elo sensitivity per game
LEADERBOARD_SIZE = 10
_anonymous_names: List[str] = []


def minigames(update: Update, context: CallbackContext) -> None:
    """Called by /minigames and the "🕹 Mini Games" sticky button. Sends the hub."""
    check_log(update, "minigames")
    locale: str = update.message.from_user.language_code
    context.bot.sendMessage(
        chat_id=update.message.chat_id,
        text=get_locale(locale, TEXT_IDS.MINI_GAMES_HEADER_TEXT_ID),
        reply_markup=InlineKeyboardMarkup(_hub_keyboard(locale)),
    )


def minigames_settings_handler(update: Update, context: CallbackContext) -> None:
    """Called by every mg_* callback. Shows the settings menu and toggles its options."""
    query = update.callback_query
    query.answer()
    locale: str = query.from_user.language_code
    user_id: int = query.from_user.id
    data: str = query.data

    if data == "mg_hub":
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.MINI_GAMES_HEADER_TEXT_ID),
            _hub_keyboard(locale),
        )
        return

    if data == "mg_setname":
        context.user_data.setdefault("minigames", {})["awaiting_name"] = True
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.MINI_GAMES_SET_NAME_PROMPT_TEXT_ID),
            _back_to_settings_keyboard(locale),
        )
        return

    if data == "mg_ranking":
        _show_ranking(context, query, locale)
        return

    if data == "mg_info":
        _show_info(context, query, locale, user_id)
        return

    if data == "mg_anon":
        set_anonymous(user_id, not is_anonymous(user_id))
    elif data == "mg_ranked":
        set_ranked(user_id, not is_ranked(user_id))

    _show_settings(context, query, locale, user_id)


def minigames_input_name(update: Update, context: CallbackContext) -> None:
    """Store the custom alias the user typed (format ``Nick: <name>``), rejecting '@'."""
    mini_games = context.user_data.get("minigames", {})
    if not mini_games.get("awaiting_name"):
        return
    check_log(update, "minigames_input_name")
    locale: str = update.message.from_user.language_code
    user_id: int = update.message.from_user.id
    name = re.sub(NAME_INPUT_PREFIX, "", update.message.text).strip()

    if not name or "@" in name:
        # keep the flag set so the next message is treated as another attempt
        context.bot.sendMessage(
            chat_id=update.message.chat_id,
            text=get_locale(locale, TEXT_IDS.MINI_GAMES_NAME_INVALID_TEXT_ID),
        )
        return

    mini_games.pop("awaiting_name", None)
    set_anonymous_name(user_id, name[:MAX_ANON_NAME_LEN])
    context.bot.sendMessage(
        chat_id=update.message.chat_id,
        text=get_locale(locale, TEXT_IDS.MINI_GAMES_NAME_SAVED_TEXT_ID),
        reply_markup=InlineKeyboardMarkup(
            _settings_keyboard(
                locale,
                is_anonymous(user_id),
                get_anonymous_name(user_id),
                is_ranked(user_id),
            )
        ),
    )


def _show_settings(context: CallbackContext, query, locale: str, user_id: int) -> None:
    _edit(
        context,
        query,
        get_locale(locale, TEXT_IDS.MINI_GAMES_SETTINGS_HEADER_TEXT_ID),
        _settings_keyboard(
            locale,
            is_anonymous(user_id),
            get_anonymous_name(user_id),
            is_ranked(user_id),
        ),
    )


def _show_info(context: CallbackContext, query, locale: str, user_id: int) -> None:
    """Show a read-only summary of the player's current profile."""
    custom_name = get_anonymous_name(user_id)
    text = get_locale(locale, TEXT_IDS.MINI_GAMES_INFO_BODY_TEXT_ID).format(
        anonymous="✅" if is_anonymous(user_id) else "❌",
        ranked="✅" if is_ranked(user_id) else "❌",
        name=custom_name if custom_name else "—",
        rating=get_rating(user_id),
    )
    _edit(context, query, text, _back_to_settings_keyboard(locale))


def _hub_keyboard(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.TRIS_GAME_NAME_TEXT_ID),
                callback_data="ttt_mode",
            )
        ],
        # chess is implemented but still a work in progress, so it is hidden from the hub
        # for now; re-add this button to expose it again
        # [
        #     InlineKeyboardButton(
        #         get_locale(locale, TEXT_IDS.CHESS_GAME_NAME_TEXT_ID),
        #         callback_data="chess_play",
        #     )
        # ],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.MINI_GAMES_RANKING_TEXT_ID),
                callback_data="mg_ranking",
            )
        ],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.MINI_GAMES_SETTINGS_TEXT_ID),
                callback_data="mg_settings",
            )
        ],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CLOSE_KEYBOARD_TEXT_ID),
                callback_data="exit_cmd",
            )
        ],
    ]


def _settings_keyboard(
    locale: str, anonymous: bool, custom_name: Optional[str], ranked: bool
) -> List[List[InlineKeyboardButton]]:
    anon_state = "✅" if anonymous else "❌"
    ranked_state = "✅" if ranked else "❌"
    if custom_name:
        name_label = f"{NINJA_ICON} {custom_name} {NINJA_ICON}"
    else:
        name_label = get_locale(locale, TEXT_IDS.MINI_GAMES_SET_NAME_TEXT_ID)
    return [
        [
            InlineKeyboardButton(
                f"{get_locale(locale, TEXT_IDS.MINI_GAMES_ANONYMOUS_TEXT_ID)} {anon_state}",
                callback_data="mg_anon",
            )
        ],
        [
            InlineKeyboardButton(
                f"{get_locale(locale, TEXT_IDS.MINI_GAMES_RANKED_TEXT_ID)} {ranked_state}",
                callback_data="mg_ranked",
            )
        ],
        [InlineKeyboardButton(name_label, callback_data="mg_setname")],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.MINI_GAMES_INFO_TEXT_ID),
                callback_data="mg_info",
            )
        ],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID),
                callback_data="mg_hub",
            )
        ],
    ]


def _back_to_settings_keyboard(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID),
                callback_data="mg_settings",
            )
        ]
    ]


def _get_settings(user_id: int) -> Optional[dict]:
    rows = DbManager.select_from(
        table_name=SETTINGS_TABLE, where="user_id = ?", where_args=(user_id,)
    )
    return rows[0] if rows else None


def is_anonymous(user_id: int) -> bool:
    """Whether ``user_id`` plays under an alias. Anonymous by default (no row yet)."""
    row = _get_settings(user_id)
    return bool(row["anonymous"]) if row else True


def get_anonymous_name(user_id: int) -> Optional[str]:
    """The user's custom alias, or None when they never set one."""
    row = _get_settings(user_id)
    return row["name"] if row and row["name"] else None


def set_anonymous(user_id: int, anonymous: bool) -> None:
    _write_settings(user_id, anonymous, get_anonymous_name(user_id))


def set_anonymous_name(user_id: int, name: str) -> None:
    _write_settings(user_id, is_anonymous(user_id), name)


def _write_settings(user_id: int, anonymous: bool, name: Optional[str]) -> None:
    DbManager.delete_from(SETTINGS_TABLE, where="user_id = ?", where_args=(user_id,))
    DbManager.insert_into(
        SETTINGS_TABLE,
        values=(user_id, int(anonymous), name),
        columns=("user_id", "anonymous", "name"),
    )


def anonymous_display_name(user_id: int) -> str:
    """The name an anonymous player is shown under: their 🥷-wrapped custom alias, or a
    random one when they never set a custom alias."""
    custom = get_anonymous_name(user_id)
    if custom:
        return f"{NINJA_ICON} {custom} {NINJA_ICON}"
    return random_anonymous_name()


def random_anonymous_name() -> str:
    """Pick a random alias for an anonymous player (names live in anonymous_names.md)."""
    return choice(_load_anonymous_names())


def _load_anonymous_names() -> List[str]:
    global _anonymous_names  # pylint: disable=global-statement
    if not _anonymous_names:
        _anonymous_names = [
            line.strip()
            for line in read_md("anonymous_names").splitlines()
            if line.strip()
        ]
    return _anonymous_names


# ---- score profile (rating, ranked preference, leaderboard); shared by every game


def _get_score(user_id: int) -> Optional[dict]:
    rows = DbManager.select_from(
        table_name=SCORE_TABLE, where="user_id = ?", where_args=(user_id,)
    )
    return rows[0] if rows else None


def is_ranked(user_id: int) -> bool:
    """Whether the player opted into ranked matches. Unranked by default (no row yet)."""
    row = _get_score(user_id)
    return bool(row["ranked"]) if row else False


def set_ranked(user_id: int, ranked: bool) -> None:
    _upsert_score(user_id, {"ranked": int(ranked)})


def get_rating(user_id: int) -> int:
    row = _get_score(user_id)
    return row["rating"] if row else DEFAULT_RATING


def ensure_score(user_id: int, first_name: Optional[str]) -> None:
    """Make sure a score row exists for the player and refresh their last-known first name.

    Called when a player enters matchmaking so both opponents already have a profile (and a
    public_id) by the time a ranked match settles.
    """
    _upsert_score(user_id, {"first_name": first_name})


def _upsert_score(user_id: int, fields: Dict[str, object]) -> None:
    """Insert a score row (filling the column defaults) or update just ``fields`` if it exists."""
    cols = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    updates = ", ".join(f"{col} = excluded.{col}" for col in fields)
    conn, cur = DbManager.get_db()
    try:
        cur.execute(
            f"INSERT INTO {SCORE_TABLE} (user_id, {cols}) VALUES (?, {placeholders}) "
            f"ON CONFLICT(user_id) DO UPDATE SET {updates}",
            (user_id, *fields.values()),
        )
        conn.commit()
    except sqlite3.Error as err:
        logger.error("minigames _upsert_score: %s", err)
    finally:
        cur.close()
        conn.close()


def apply_match_result(
    winner_id: int, loser_id: int, draw: bool = False
) -> Dict[int, Tuple[int, int]]:
    """Update both players' Elo ratings for a finished ranked match.

    Returns ``{user_id: (new_rating, delta)}`` so each game can show the change to both players.
    """
    r_win = get_rating(winner_id)
    r_lose = get_rating(loser_id)
    expected_win = 1 / (1 + 10 ** ((r_lose - r_win) / 400))
    score_win, score_lose = (0.5, 0.5) if draw else (1.0, 0.0)
    new_win = round(r_win + K_FACTOR * (score_win - expected_win))
    new_lose = round(r_lose + K_FACTOR * (score_lose - (1 - expected_win)))
    _record_rating(winner_id, new_win, "draw" if draw else "win")
    _record_rating(loser_id, new_lose, "draw" if draw else "loss")
    return {
        winner_id: (new_win, new_win - r_win),
        loser_id: (new_lose, new_lose - r_lose),
    }


def _record_rating(user_id: int, rating: int, result: str) -> None:
    column = {"win": "wins", "loss": "losses", "draw": "draws"}[result]
    conn, cur = DbManager.get_db()
    try:
        cur.execute(
            f"INSERT INTO {SCORE_TABLE} (user_id, rating, {column}) VALUES (?, ?, 1) "
            f"ON CONFLICT(user_id) DO UPDATE SET rating = excluded.rating, "
            f"{column} = {column} + 1",
            (user_id, rating),
        )
        conn.commit()
    except sqlite3.Error as err:
        logger.error("minigames _record_rating: %s", err)
    finally:
        cur.close()
        conn.close()


def rating_change_text(rating: int, delta: int, locale: str) -> str:
    return get_locale(locale, TEXT_IDS.MINI_GAMES_RATING_CHANGE_TEXT_ID).format(
        rating=rating, change=f"{delta:+d}"
    )


def opponent_text(opponent_label: str, locale: str) -> str:
    return get_locale(locale, TEXT_IDS.MINI_GAMES_OPPONENT_TEXT_ID).format(
        player=opponent_label
    )


def you_are_text(player_label: str, locale: str) -> str:
    return get_locale(locale, TEXT_IDS.MINI_GAMES_YOU_ARE_TEXT_ID).format(
        player=player_label
    )


def _leaderboard_rows() -> List[dict]:
    rows = DbManager.select_from(
        table_name=SCORE_TABLE,
        where="(wins + losses + draws) > 0",
        order_by="rating DESC",
    )
    return rows[:LEADERBOARD_SIZE]


def _leaderboard_name(row: dict, locale: str) -> str:
    """How a player is listed: real name if public, custom alias if set, else a public id."""
    user_id = row["user_id"]
    if not is_anonymous(user_id) and row["first_name"]:
        return f"{GRADUATE_ICON} {row['first_name']}"
    custom = get_anonymous_name(user_id)
    if custom:
        return f"{NINJA_ICON} {custom} {NINJA_ICON}"
    return get_locale(locale, TEXT_IDS.MINI_GAMES_ANON_PLAYER_TEXT_ID).format(
        id=row["public_id"]
    )


def _show_ranking(context: CallbackContext, query, locale: str) -> None:
    rows = _leaderboard_rows()
    if not rows:
        text = get_locale(locale, TEXT_IDS.MINI_GAMES_RANKING_EMPTY_TEXT_ID)
    else:
        lines = [get_locale(locale, TEXT_IDS.MINI_GAMES_RANKING_HEADER_TEXT_ID), ""]
        for rank, row in enumerate(rows, start=1):
            lines.append(f"{rank}. {_leaderboard_name(row, locale)} — {row['rating']}")
        text = "\n".join(lines)
    _edit(context, query, text, _back_to_hub_keyboard(locale))


def _back_to_hub_keyboard(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID),
                callback_data="mg_hub",
            )
        ]
    ]


def _edit(
    context: CallbackContext,
    query,
    text: str,
    keyboard: List[List[InlineKeyboardButton]],
) -> None:
    context.bot.editMessageText(
        text=text,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
