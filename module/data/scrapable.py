"""Scrapable abstract class"""
from module.data.db_manager import DbManager


class Scrapable():
    """Abstract class base of everything that is to be scraped and saved in the database"""

    @property
    def table(self):
        """:class:`str`: name of the database table that will store this Scrapable"""
        raise NotImplementedError("table is to be implemented")

    @property
    def columns(self):
        """:class:`tuple`: tuple of column names of the database table that will store this Scrapable"""
        raise NotImplementedError("columns is to be implemented")

    @property
    def values(self):
        """:class:`tuple`: tuple of values that will be saved in the database"""
        raise NotImplementedError("values is to be implemented")

    def save(self):
        """Save this scrapable object in the database"""
        DbManager.insert_into(table_name=self.table, columns=self.columns, values=self.values)

    @classmethod
    def bulk_save(cls, scrapables: list):
        """Saves multiple Scrapable objects at once in the database

        Args:
            scrapables (:class:`list`): list of Scrapable objects to save
        """
        if scrapables is None:
            return
        values = tuple(scrapable.values for scrapable in scrapables)
        DbManager.insert_into(table_name=scrapables[0].table, columns=scrapables[0].columns, values=values, multiple_rows=True)
