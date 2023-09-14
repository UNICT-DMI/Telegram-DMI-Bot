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