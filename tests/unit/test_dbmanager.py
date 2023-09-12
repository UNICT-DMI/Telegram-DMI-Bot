import pytest
import yaml
from module.data import DbManager


TABLE_NAME = "test_table"

@pytest.fixture(scope="class")
def test_results() -> dict:
    """Called at the beginning of test session.
        Initialize the database to be tested

    Args:
        init_test_db: database to initialize         
    """

    DbManager.query_from_file(filename="data/DB_TEST.sql")

    with open("tests/unit/db_results.yaml", 'r', encoding='utf-8') as yaml_results:
        results = yaml.load(yaml_results, Loader=yaml.SafeLoader)
    yield results

    DbManager.query_from_string("DROP DATABASE IF EXISTS test_table")


class TestDb:
    def test_get_db(self) -> None:
        """Test get_db function"""

        conn, cur = DbManager.get_db()

        assert conn is not None
        assert cur is not None

    def test_query_from_string(self) -> None:
        """Test query_from_string function"""

        DbManager.query_from_string("CREATE TABLE IF NOT EXISTS temp(id INT PRIMARY KEY);")

        assert DbManager.count_from(table_name="temp") == 0

        DbManager.query_from_string("DROP TABLE IF EXISTS temp;")


    def test_select_from(self, test_results: dict) -> None:
        """Test select_from function"""

        curr_results = DbManager.select_from(table_name=TABLE_NAME, where="id = ? OR id = ?", where_args=(2, 4))
        assert curr_results == test_results["select_from_1"]

        curr_results = DbManager.select_from(table_name=TABLE_NAME, select="id, string2", where="id = 3")
        assert curr_results == test_results["select_from_2"]

        curr_results = DbManager.select_from(table_name=TABLE_NAME, select="string1")
        assert curr_results == test_results["select_from_3"]


    def test_count_from(self, test_results: dict) -> None:
        """Test count_from function"""

        num_rows = DbManager.count_from(table_name=TABLE_NAME, where="id > ?", where_args=(2,))
        assert num_rows == test_results["count_from_1"]

        num_rows = DbManager.count_from(table_name=TABLE_NAME, select="string2", where="id = ?", where_args=(3,))
        assert num_rows == test_results["count_from_2"]

        num_rows = DbManager.count_from(table_name=TABLE_NAME, select="string1")
        assert num_rows == test_results["count_from_3"]


    def test_insert_into(self, test_results: dict) -> None:
        """Test insert_into function"""

        DbManager.insert_into(table_name=TABLE_NAME, values=(7, "test_insert_into1", "TEST_INSERT_INTO1"), columns=("id", "string1", "string2"))
        DbManager.insert_into(table_name=TABLE_NAME, values=(8, "test_insert_into2", "TEST_INSERT_INTO2"), columns=("id", "string1", "string2"))
        DbManager.insert_into(table_name=TABLE_NAME, values=((9, "test_insert_into3", "TEST_INSERT_INTO3"), (10, "test_insert_into4", "TEST_INSERT_INTO4")), columns=("id", "string1", "string2"), multiple_rows=True)

        curr_results = DbManager.select_from(table_name=TABLE_NAME, where="id >= ?", where_args=(7,))

        assert curr_results == test_results["insert_into"]

    def test_delete_from(self, test_results: dict) -> None:
        """Test delete_from function"""

        DbManager.delete_from(table_name=TABLE_NAME, where="id <= ?", where_args=(2,))
        count = DbManager.count_from(table_name=TABLE_NAME, where="id >= ?", where_args=(2,))
        assert count == test_results["delete_from_1"]

        DbManager.delete_from(table_name=TABLE_NAME, where="id >= ?", where_args=(2,))
        count = DbManager.count_from(table_name=TABLE_NAME, where="id >= ?", where_args=(2,))
        assert count == test_results["delete_from_2"]