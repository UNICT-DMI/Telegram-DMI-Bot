-- stat_list
CREATE TABLE IF NOT EXISTS stat_list (
	Type varchar(100),
	chat_id int(100),
	DateCommand DATE
);

-- professors
CREATE TABLE IF NOT EXISTS `professors` (
  "ID" INT(11) NOT NULL PRIMARY KEY,
  "ruolo" VARCHAR(255),
  "nome" VARCHAR(255),
  "scheda_dmi" VARCHAR(255),
  "fax" VARCHAR(255),
  "telefono" VARCHAR(255),
  "email" VARCHAR(255),
  "ufficio" VARCHAR(255),
  "sito" VARCHAR(255),
  "photo_id" VARCHAR(255)
);

-- lessons
CREATE TABLE IF NOT EXISTS `lessons` (
  `nome` VARCHAR(255),
  `giorno_settimana` VARCHAR(255),
  `ora_inizio` VARCHAR(255),
  `ora_fine` VARCHAR(255),
  `aula` INT(4),
  `anno` INT(1),
  `semestre` VARCHAR(255)
);

-- exams
CREATE TABLE IF NOT EXISTS `exams` (
  `anno` INT(2),
  `cdl` VARCHAR(255),
  `docenti` VARCHAR(255),
  `insegnamento` VARCHAR(255),
  `prima` VARCHAR(255),
  `seconda` VARCHAR(255),
  `terza` VARCHAR(255),
  `straordinaria` VARCHAR(255)
);

-- exams registrations
CREATE TABLE IF NOT EXISTS `exams_reg` (
  `studenti` VARCHAR(255),
  `insegnamento` VARCHAR(255),
  `docenti` VARCHAR(255),
  'data' DATE,
  `lingua` VARCHAR(255),
  PRIMARY KEY('studenti', 'insegnamento', 'docenti')
);

-- timetable_slots
CREATE TABLE IF NOT EXISTS `timetable_slots` (
  `ID` INTEGER PRIMARY KEY,
  `nome` VARCHAR(255) NOT NULL,
  `giorno` INT(4) NOT NULL,
  `ora_inizio` VARCHAR(255) NOT NULL,
  `ora_fine` VARCHAR(255) NOT NULL,
  `aula` VARCHAR(255) NOT NULL
);

-- gitlab
CREATE TABLE IF NOT EXISTS `gitlab` (
  `id` TEXT NOT NULL UNIQUE,
  `parent_id` INTEGER,
  `pathname` TEXT,
  `web_url` TEXT,
  `name` TEXT,
  `type` TEXT NOT NULL,
  PRIMARY KEY(`id`)
);

--stickers
CREATE TABLE IF NOT EXISTS `stickers` (
'id' TEXT
);

INSERT INTO 'stickers' VALUES
("CAADBAADSAADkwaxAu__-caLSsmjAg"),
("CAADBAADKwYAApMGsQKwAAGAxFt4ZJUC"),
("CAADBAADxwYAApMGsQLGwk3pD84glQI"),
("CAADBAADSgADkwaxApCmKWBdoISdAg"),
("CAADBAADTAADkwaxArmUi8vyHXHoAg"),
("CAADBAADWAADkwaxApksn5fQKht3Ag"),
("CAADBAADXwADkwaxAuxuCh6-zE1OAg"),
("CAADBAADWgQAApMGsQLMO_NaIYiyQgI"),
("CAADBAADXAQAApMGsQIjmmICforzsgI"),
("CAADBAADdQQAApMGsQK481D0Yiy-ugI"),
("CAADBAAD8gQAApMGsQJGiQerTyOvXgI"),
("CAADBAADIQUAApMGsQLdqE-X0ulTAAEC"),
("CAADBAADCAYAApMGsQK3Wmjnr3hS-gI"),
("CAADBAADKQYAApMGsQK4T3CvFIEk-wI");

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

-- chess live games (state as a FEN string; w_ is the white player, b_ the black one).
-- white_captured/black_captured accumulate the symbols of the pieces each side has taken,
-- last_san is the SAN of the latest move shown to both players.
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
