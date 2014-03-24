"""
    leaderboard.persistence.user
    =============================

    Implements :class:`UserRepository`, for :class:`User` objects.

    :author: Michael Browning
"""

import psycopg2

from .repository import Repository
from ..model import User
from ..model.effort import Effort
from ..model.location import Location
from ..exceptions import ConstraintError
from . import opens_cursor


class UserRepository(Repository):
    """A repository that keeps track of :class:`User` objects."""

    table_name = 'users'
    efforts_table_name = 'efforts'
    locations_table_name = 'locations'
    users2teams_table_name = 'users2teams'

    def __init__(self, connection=None):
        super(UserRepository, self).__init__(connection)
        self.get = opens_cursor(self.get, self.connection)
        self.save = opens_cursor(self.save, self.connection)
        self.delete = opens_cursor(self.delete, self.connection)
        self.set_team = opens_cursor(self.set_team, self.connection)
        self.get_team = opens_cursor(self.get_team, self.connection)

    def get(self, cursor, username=None, user_id=None):
        """Get the :class:`User` with the specified username or id.

        :param username: the string username of the :class:`User`
        :param id: the integer id of the :class:`User`
        """
        if username and user_id:
            raise ValueError('Only one of id or username may be used as index')
        elif username:
            field = 'username'
            value = username
        elif user_id:
            field = 'id'
            value = user_id
        else:
            raise ValueError('One of id or username must be used as index')

        try:
            user_data = self._get(cursor, field, value)[0]
        except IndexError:
            return

        user_id = user_data['id']
        del user_data['id']

        user = User(**user_data)
        user.id = user_id
        for e in self._get_efforts(cursor, user):
            user.add_effort(e)

        return user

    def save(self, cursor, user):
        """Save a :class:`User` to the repository.

        :param user: a :class:`User` object
        """
        if hasattr(user, 'id'):
            self._update(cursor, user)
        else:
            try:
                cursor.execute(
                    'INSERT INTO %s (username, first_name, last_name, email) '
                    'VALUES (%%s, %%s, %%s, %%s) RETURNING id' % (
                        self.table_name,
                    ),
                    (
                        user.username,
                        user.first_name,
                        user.last_name,
                        user.email,
                    )
                )
            except psycopg2.IntegrityError:
                raise ConstraintError('user %s exists' % user.username)

            user.id = cursor.fetchone()['id']

            for e in user.efforts:
                self._save_effort(cursor, e, user)

    def delete(self, cursor, user):
        """Delete a :class:`User` from the repository.

        :param user: a :class:`User` object
        """
        cursor.execute(
            'DELETE FROM %s WHERE id = %%s' % self.table_name, (user.id,)
        )
        self._delete_efforts(cursor, user)

    def set_team(self, cursor, user, team):
        """Set a user's team.

        :param user: the user to update
        :param team: the team to add the user to
        """
        if hasattr(team, 'id'):
            team_id = team.id
        else:
            team_id = int(team)
        cursor.execute(
            'UPDATE %s SET team = %%s WHERE "user" = %%s' % (
                self.users2teams_table_name
            ),
            (team_id, user.id)
        )

    def get_team(self, cursor, user):
        """Get the id of a user's team.

        :param user: the user to retrieve the team of
        """
        cursor.execute(
            'SELECT team FROM %s WHERE "user" = %%s' % (
                self.users2teams_table_name
            ),
            (user.id,)
        )

        return cursor.fetchone()['team']

    def _update(self, cursor, user):
        """Update a user's data.

        :param user: the user to be updated
        """
        existing = self.get(user_id=user.id)
        # This whole bit feels ugly, but I'm tired.
        changed = []
        for field in ('username', 'first_name', 'last_name', 'email'):
            if getattr(user, field) != getattr(existing, field):
                changed.append(field)
        if changed:
            placeholders = ', '.join(
                ['%s = %%s' % field for field in changed]
            )
            cursor.execute(
                'UPDATE %s SET %s WHERE id = %%s' % (
                    self.table_name, placeholders
                ),
                tuple([getattr(user, field) for field in changed] + [user.id])
            )

        for e in user.efforts - existing.efforts:
            self._save_effort(cursor, e, user)
        for e in existing.efforts - user.efforts:
            self._delete_effort(cursor, e, user)

    def _create(self, cursor, row):
        """Reconstitute a user from a database row.

        :param row: row data as dictionary
        """
        user = User(
            username=row['username'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            email=row['email']
        )
        user.id = row['id']

        for e in self._get_efforts(cursor, user):
            user.add_effort(e)

        return user

    def _get_efforts(self, cursor, user):
        """Get the efforts associated with an existing user in the database.

        :param user: the :class:`User` to retrieve efforts for
        """
        cursor.execute(
            'SELECT * FROM %s WHERE "user" = %%s' % self.efforts_table_name,
            (user.id,)
        )
        for e in cursor:
            yield self._create_effort(cursor, **e)

    def _delete_efforts(self, cursor, user):
        """Delete the efforts associated with an existing user in the database.

        :param user: the :class:`User` to delete efforts for
        """
        cursor.execute(
            'DELETE FROM %s WHERE "user" = %%s' % self.efforts_table_name,
            (user.id,)
        )

    def _create_effort(self, cursor, **kwargs):
        """Create an effort from a database row."""
        location = self._get_location(cursor, kwargs['location'])
        effort = Effort(
            start_time=kwargs['start_time'],
            duration=kwargs['duration'],
            location=location
        )

        return effort

    def _save_effort(self, cursor, effort, user):
        """Insert an effort associated with a given user into the database.

        :param effort: the :class:`Effort` to be inserted
        :param user: the :class:`User` associated with that effort
        """
        if not hasattr(effort.location, 'id'):
            self._save_location(cursor, effort.location)

        try:
            cursor.execute(
                'INSERT INTO %s (start_time, duration, "user", location) '
                    'VALUES (%%s, %%s, %%s, %%s)' % (self.efforts_table_name),
                (
                    effort.start_time,
                    effort.duration,
                    user.id,
                    effort.location.id
                )
            )
        except psycopg2.IntegrityError:
            pass

    def _delete_effort(self, cursor, effort, user):
        """Delete an effort associated with a given user from the database.

        :param effort: an object of type :class:`Effort`
        :param user: the :class:`User` associated with the effort
        """
        cursor.execute(
            'DELETE FROM %s WHERE '
                'start_time = %%s AND '
                'duration = %%s AND '
                '"user" = %%s AND '
                'location = %%s' % self.efforts_table_name,
            (effort.start_time, effort.duration, effort.location.id, user.id)
        )

    def _get_location(self, cursor, location_id):
        """Get a location from the database by supplied id.

        :param location_id: the id of the location
        """
        cursor.execute(
            'SELECT * FROM %s WHERE id = %%s' % self.locations_table_name,
            (location_id,)
        )
        location_data = cursor.fetchone()
        if location_data:
            del location_data['id']
            location = Location(**location_data)
            location.id = location_id

            return location

    def _save_location(self, cursor, location):
        """Insert a location into the database and update its id.

        :param location: the :class:`Location` to be inserted
        """
        try:
            cursor.execute(
                'INSERT INTO %s (latitude, longitude) VALUES (%%s, %%s) '
                    'RETURNING id' % self.locations_table_name,
                (location.latitude, location.longitude)
            )
        except psycopg2.IntegrityError:
            cursor.execute(
                'SELECT id FROM %s WHERE latitude = %%s AND longitude = %%s' % (
                    self.locations_table_name
                ),
                (location.latitude, location.longitude)
            )
        location.id = cursor.fetchone()['id']
