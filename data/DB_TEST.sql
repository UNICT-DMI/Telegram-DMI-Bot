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