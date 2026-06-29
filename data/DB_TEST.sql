--test table
--(DROP TABLE IF EXISTS test_table);

CREATE TABLE IF NOT EXISTS test_table (
    `id` INT PRIMARY KEY,
    `string1` varchar(50) NOT NULL,
    `string2` varchar(50) NOT NULL
);

INSERT INTO test_table (`id`, `string1`, `string2`) VALUES 
(1, "test1", "TEST1"),
(2, "test2", "TEST2"),
(3, "test3", "TEST3"),
(4, "test4", "TEST4");

-- mini games matchmaking queue (shared by every game, tagged by the `game` column)
CREATE TABLE IF NOT EXISTS `minigames_queue` (
  `game` TEXT NOT NULL,
  `user_id` INTEGER NOT NULL,
  `chat_id` INTEGER NOT NULL,
  `message_id` INTEGER NOT NULL,
  `name` TEXT NOT NULL,
  `locale` TEXT,
  `queued_at` REAL NOT NULL,
  PRIMARY KEY (`game`, `user_id`)
);

-- mini games per-user settings (shared by every game)
CREATE TABLE IF NOT EXISTS `minigames_settings` (
  `user_id` INTEGER PRIMARY KEY,
  `anonymous` INTEGER NOT NULL DEFAULT 1,
  `name` TEXT
);

-- mini games completed-match log (one row per finished match)
CREATE TABLE IF NOT EXISTS `minigames_match_log` (
  `game` TEXT NOT NULL,
  `finished_at` DATE NOT NULL
);

-- mini games per-user score profile (shared by every game)
CREATE TABLE IF NOT EXISTS `minigames_score` (
  `public_id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL UNIQUE,
  `first_name` TEXT,
  `rating` INTEGER NOT NULL DEFAULT 1000,
  `wins` INTEGER NOT NULL DEFAULT 0,
  `losses` INTEGER NOT NULL DEFAULT 0,
  `draws` INTEGER NOT NULL DEFAULT 0,
  `ranked` INTEGER NOT NULL DEFAULT 0
);

-- tris (tic-tac-toe) live games (game-specific board and player columns)
CREATE TABLE IF NOT EXISTS `tris_game` (
  `game_id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `board` TEXT NOT NULL,
  `x_user_id` INTEGER NOT NULL,
  `x_chat_id` INTEGER NOT NULL,
  `x_message_id` INTEGER NOT NULL,
  `x_name` TEXT NOT NULL,
  `x_locale` TEXT,
  `o_user_id` INTEGER NOT NULL,
  `o_chat_id` INTEGER NOT NULL,
  `o_message_id` INTEGER NOT NULL,
  `o_name` TEXT NOT NULL,
  `o_locale` TEXT,
  `updated_at` REAL NOT NULL
);

-- chess live games (state as a FEN string; w_ is the white player, b_ the black one)
CREATE TABLE IF NOT EXISTS `chess_game` (
  `game_id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `fen` TEXT NOT NULL,
  `white_captured` TEXT NOT NULL DEFAULT '',
  `black_captured` TEXT NOT NULL DEFAULT '',
  `last_san` TEXT,
  `w_user_id` INTEGER NOT NULL,
  `w_chat_id` INTEGER NOT NULL,
  `w_message_id` INTEGER NOT NULL,
  `w_name` TEXT NOT NULL,
  `w_locale` TEXT,
  `b_user_id` INTEGER NOT NULL,
  `b_chat_id` INTEGER NOT NULL,
  `b_message_id` INTEGER NOT NULL,
  `b_name` TEXT NOT NULL,
  `b_locale` TEXT,
  `updated_at` REAL NOT NULL
);