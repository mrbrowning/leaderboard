"""
    leaderboard.persistence
    ========================

    Implements the persistence logic for domain model objects.

    :author: Michael Browning
"""

from functools import wraps
from psycopg2.extras import RealDictCursor


def opens_cursor(fn, connection):
    """Wraps a function that accepts a cursor as its first argument, handling
    the opening, closing and commit logic.

    :param fn: the function to wrap
    :param connection: the connection that spawns the cursor
    """
    @wraps(fn)
    def wrapped(*args, **kwargs):
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        result = fn(cursor, *args, **kwargs)
        connection.commit()
        cursor.close()

        return result

    return wrapped


from .user import UserRepository
from .team import TeamRepository
