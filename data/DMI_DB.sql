-- chat_id_list
CREATE TABLE IF NOT EXISTS `Chat_id_List` (
  `id` INTEGER PRIMARY KEY,
  `Chat_id` int(11) NOT NULL,
  `Username` text NOT NULL,
  `Nome` int(11) NOT NULL,
  `Cognome` int(11) NOT NULL,
  `E-mail` int(11) NOT NULL
);

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
  "cognome" VARCHAR(255),
  "scheda DMI" VARCHAR(255),
  "fax" VARCHAR(255),
  "telefono" VARCHAR(255),
  "email" VARCHAR(255),
  "ufficio" VARCHAR(255),
  "sito" VARCHAR(255)
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
