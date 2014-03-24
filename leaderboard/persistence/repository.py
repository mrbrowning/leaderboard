"""
    leaderboard.persistence.repository
    ===================================

    Defines the abstract :class:`Repository`.

    :author: Michael Browning
"""

import os
import urlparse
import psycopg2

from . import opens_cursor
from .. import config


class Repository(object):
    """A repository that keeps track of persisted domain objects."""

    def __init__(self, connection=None):
        if connection is None:
            from .. import connection as conn
            self.connection = conn
        else:
            self.connection = connection
        self.all = opens_cursor(self.all, self.connection)

    def all(self, cursor):
        """Return all objects in the repository."""
        cursor.execute('SELECT * FROM %s' % self.table_name)

        return [self._create(cursor, r) for r in cursor.fetchall()]

    def get(self, obj_id):
        """Return an object with the specified id from the repository.

        :param obj_id: the id of the object
        """
        raise NotImplementedError()

    def save(self, obj):
        """Save an object to the repository.

        :param obj: the domain object to save
        """
        raise NotImplementedError()

    def delete(self, obj):
        """Delete an object from the repository.

        :param obj: the object to delete
        """
        raise NotImplementedError()

    def _get(self, cursor, field, value):
        """Get the objects with the specified value in the specified field.

        :param field: the field to search
        :param value: the desired value
        """
        cursor.execute(
            'SELECT * FROM %s WHERE %s = %%s' % (self.table_name, field),
            (value,)
        )

        return cursor.fetchall()
