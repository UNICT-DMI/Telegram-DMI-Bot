"""Scrapable abstract class"""
from module.data.db_manager import DbManager


class Scrapable():
    """Abstract class base of everything that is to be scraped and saved in the database"""

    @property
    def table(self):
        """name of the database table that will store this Scrapable"""
        raise NotImplementedError("table is to be implemented")

    @property
    def columns(self):
        """tuple of column names of the database table that will store this Scrapable"""
        raise NotImplementedError("columns is to be implemented")

    @property
    def values(self):
        """tuple of values that will be saved in the database"""
        # pylint: disable=unnecessary-dunder-call
        return tuple(self.__getattribute__(column) for column in self.columns)

    def save(self):
        """Saves this scrapable object in the database"""
        DbManager.insert_into(table_name=self.table, columns=self.columns, values=self.values)

    def delete(self):
        """Deletes this scrapable object from the database"""
        where = " = ? and ".join(self.columns) + " = ?"
        DbManager.delete_from(table_name=self.table, where=where, where_args=self.values)

    @classmethod
    def bulk_save(cls, scrapables: list):
        """Saves multiple Scrapable objects at once in the database

        Args:
            scrapables: list of Scrapable objects to save
        """
        if scrapables is None:
            return
        values = tuple(scrapable.values for scrapable in scrapables)
        if len(values) == 0:
            return # nothing to save

        DbManager.insert_into(table_name=cls().table, columns=cls().columns, values=values, multiple_rows=True)

    @classmethod
    def _find(cls, **kwargs) -> list:
        """Produces a list of scrapables from the database, based on the provided parametes

        Returns:
            result of the query on the database
        """
        where = "and".join((f" {c} = ? " for c in kwargs))
        values = tuple(v for v in kwargs.values())
        db_results = DbManager.select_from(table_name=cls().table, where=where, where_args=values)
        return cls._query_result_initializer(db_results)

    @classmethod
    def find_all(cls) -> list:
        """Finds all the scrapable objects present in the database

        Returns:
            list of all the scrapable objects
        """
        db_results = DbManager.select_from(table_name=cls().table)
        return cls._query_result_initializer(db_results)

    @classmethod
    def count(cls, where: str = "", where_args: tuple = None, group_by: str = "") -> int:
        """Count the number of scrapable objects present in the database, based on the parameters

        Args:
            where: where clause, with ? placeholders for the where_args. Defaults to "".
            where_args: args used in the where clause. Defaults to None.
            group_by: group by clause. Defaults to "".

        Returns:
            number of scrapable objects
        """
        return DbManager.count_from(table_name=cls().table, where=where, where_args=where_args, group_by=group_by)

    @classmethod
    def delete_all(cls):
        """Deletes all the scrapable objects of this kind from the database"""
        DbManager.delete_from(table_name=cls().table)

    @classmethod
    def _query_result_initializer(cls, db_results: list) -> list:
        """Initializes the list of scrapables from the result of the query on the database

        Args:
            db_results: list of rows produced by the database query

        Returns:
            list of initialized scrapable objects
        """
        scrapables = []
        for row in db_results:
            scrapable = cls()
            for col in scrapable.columns:
                setattr(scrapable, col, row.get(col, None))
            scrapables.append(scrapable)
        return scrapables

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise NotImplementedError()
        return self.values == other.values

    def __hash__(self):
        return hash(self.values)
