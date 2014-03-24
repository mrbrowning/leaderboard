"""
    leaderboard.persistence.team
    =============================

    Implements :class:`TeamRepository`, for :class:`Team` objects.

    :author: Michael Browning
"""

import psycopg2

from .repository import Repository
from .user import UserRepository
from ..model import Team
from . import opens_cursor
from ..exceptions import ConstraintError


class TeamRepository(Repository):
    """A repository that keeps track of :class:`Team` objects."""

    table_name = 'teams'

    def __init__(self, connection=None):
        super(TeamRepository, self).__init__(connection)
        self.get = opens_cursor(self.get, self.connection)
        self.save = opens_cursor(self.save, self.connection)
        self.delete = opens_cursor(self.delete, self.connection)
        self.user_repository = UserRepository(self.connection)

    def get(self, cursor, team_id=None, name=None):
        """Get the :class:`Team` with the specified id or name.

        :param team_id: the integer id of the team
        :param name: the name of the team
        """
        if name and team_id:
            raise ValueError('Only one of id or name may be used as index')
        elif name:
            field = 'name'
            value = name
        elif team_id:
            field = 'id'
            value = team_id
        else:
            raise ValueError('One of id or name must be used as index')

        try:
            team_data = self._get(cursor, field, value)[0]
        except IndexError:
            return

        team_id = team_data['id']
        del team_data['id']

        team = Team(**team_data)
        team.id = team_id
        for u in self._get_users(cursor, team):
            team.add_user(u)

        return team

    def save(self, cursor, team):
        """Save a :class:`Team` to the repository.

        :param team: a :class:`Team` object
        """
        if hasattr(team, 'id'):
            self._update(cursor, team)
        else:
            try:
                cursor.execute(
                    'INSERT INTO %s (name) VALUES (%%s) RETURNING id' % (
                        self.table_name,
                    ),
                    (team.name,)
                )
            except psycopg2.IntegrityError:
                raise ConstraintError('team %s exists' % team.name)

            team.id = cursor.fetchone()['id']

        for user in team:
            self.user_repository.save(user)

    def delete(self, cursor, team):
        """Delete a :class:`Team` from the repository.

        :param team: the team to delete
        """
        if len(team):
            raise ConstraintError('A team with users cannot be deleted')

        cursor.execute(
            'DELETE FROM %s WHERE id = %%s' % self.table_name, (team.id,)
        )

    def _create(self, cursor, row):
        """Reconstitute a team from a database row.

        :param row: the row data as a dictionary
        """
        team = Team(name=row['name'])
        team.id = row['id']

        for u in self._get_users(cursor, team):
            team.add_user(u)

        return team

    def _update(self, cursor, team):
        """Update an existing team's data.

        :param team: the team to update
        """
        existing = self.get(team_id=team.id)
        if team.name != existing.name:
            cursor.execute(
                'UPDATE %s SET name = %%s WHERE id = %%s' % self.table_name,
                (team.name, team.id)
            )

        existing_users = set(u for u in existing)
        new_users = set(u for u in team)

        for u in new_users - existing_users:
            self.user_repository.save(u)
            self.user_repository.set_team(u, team)

    def _get_users(self, cursor, team):
        """Return users associated with a team.

        :param team: the team to get users for
        """
        cursor.execute(
            'SELECT "user" FROM %s WHERE team = %%s' % (
                self.user_repository.users2teams_table_name
            ),
            (team.id,)
        )

        for user_data in cursor.fetchall():
            yield self.user_repository.get(user_id=user_data['user'])
