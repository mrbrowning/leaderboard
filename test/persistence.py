"""
    test.persistence
    ================

    Test persistence logic.

    :author: Michael Browning
"""

import unittest

import psycopg2

from leaderboard.persistence.repository import Repository
from leaderboard.persistence import UserRepository, TeamRepository
from leaderboard.model.location import Location
from leaderboard.exceptions import ConstraintError


class RepositoryTestCase(unittest.TestCase):
    """Test the base :class:`leaderboard.persistence.Repository`."""

    def test_all(self):
        """Test :meth:`Repository.all`"""
        class TestAllCursor(TestCursor):
            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query, 'SELECT * FROM test'
                )

            def fetchall(self):
                return [1]

        repository = TestRepository(TestConnection(TestAllCursor, self))
        all_objs = repository.all()

    def test__get(self):
        """Test :meth:`Repository._get`"""
        class TestGetCursor(TestCursor):
            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query, 'SELECT * FROM test WHERE field = %s'
                )
                self.test_case.assertEqual(params, ('value',))

        repository = TestRepository(TestConnection(TestCursor, self))
        get = repository._get(TestGetCursor(self), 'field', 'value')


class UserRepositoryTestCase(unittest.TestCase):
    """Test :class:`leaderboard.persistence.UserRepository`"""

    def test__get_location(self):
        """Test that :meth:`UserRepository._get_location` returns a location"""
        class TestGetLocationCursor(TestCursor):
            fields = {'latitude': 41.5, 'longitude': 73.5}

            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query, 'SELECT * FROM locations WHERE id = %s'
                )
                self.id = params[0]

            def fetchone(self):
                if self.id == 1:
                    fields = self.fields.copy()
                    fields['id'] = 1
                    return fields

        connection = TestConnection(TestGetLocationCursor, self)
        repository = UserRepository(connection)
        location = repository._get_location(connection.cursor(), 1)
        self.assertEqual(
            TestGetLocationCursor.fields,
            {k: getattr(location, k) for k in
                TestGetLocationCursor.fields.keys()}
        )
        self.assertEqual(
            repository._get_location(connection.cursor(), 5),
            None
        )

    def test__save_location(self):
        """Test that :meth:`UserRepository._save_location` saves a location"""
        class TestSaveLocationCursor(TestCursor):
            fields = {'latitude': 41.5, 'longitude': 73.5}
            id = 10

            def execute(self, query, params=None):
                if query.startswith('INSERT'):
                    self.test_case.assertEqual(
                        query,
                        'INSERT INTO locations (latitude, longitude) '
                            'VALUES (%s, %s) RETURNING id'
                    )
                    raise psycopg2.IntegrityError()
                else:
                    self.test_case.assertEqual(
                        query,
                        'SELECT id FROM locations WHERE '
                            'latitude = %s AND longitude = %s'
                    )
                self.test_case.assertEqual(
                    params,
                    (self.fields['latitude'], self.fields['longitude'])
                )

            def fetchone(self):
                return {'id': self.id}

        connection = TestConnection(TestSaveLocationCursor, self)
        repository = UserRepository(connection)
        location = Location(**TestSaveLocationCursor.fields)
        repository._save_location(connection.cursor(), location)

        self.assertEqual(location.id, TestSaveLocationCursor.id)

    def test__get_efforts(self):
        """Test that :meth:`UserRepository._get_efforts` returns a list of
        objects of class :class:`Effort` associated with the user
        """

        class TestRepository(UserRepository):
            def _create_effort(self, cursor, **kwargs):
                self.test_case.assertEqual(kwargs, cursor.fields)
                return kwargs

        class TestGetEffortsCursor(TestCursor):
            fields = {'field': 'value'}

            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query, 'SELECT * FROM efforts WHERE "user" = %s'
                )
                self.test_case.assertEqual(
                    params, (1,)
                )

            def __iter__(self):
                self.iter = iter([self.fields])
                return self.iter

            def next(self):
                return self.iter.next()

        class TestUser(object):
            def __init__(self):
                self.id = 1


        connection = TestConnection(TestGetEffortsCursor, self)
        repository = TestRepository(connection)
        repository.test_case = self

        self.assertEqual(
            [i for i in repository._get_efforts(
                connection.cursor(), TestUser()
            )],
            [TestGetEffortsCursor.fields]
        )

    def test__create_effort(self):
        """Test that :meth:`UserRepository._create_effort` creates an effort"""
        import leaderboard.persistence.user as ur_module
        from copy import copy

        class TestEffort(object):
            def __init__(self, **kwargs):
                self.test_case.assertEqual(kwargs, self.fields)

        class TestLocation(object):
            def __init__(self):
                self.id = 1

            def __eq__(self, other):
                return self.id == other.id

        class TestRepository(UserRepository):
            location = TestLocation()
            fields = {
                'start_time': 'test_st',
                'duration': 'test_d',
                'location': TestLocation(),
            }

            def _get_location(self, cursor, location_id):
                self.test_case.assertEqual(location_id, 1)
                return self.location

        TestEffort.test_case = self
        TestEffort.fields = TestRepository.fields
        ur_module.Effort = TestEffort
        TestRepository.test_case = self

        fields = copy(TestRepository.fields)
        fields['location'] = 1

        repository = TestRepository(TestConnection(TestCursor, self))
        effort = repository._create_effort(TestCursor(self), **fields)
        self.assertIsInstance(effort, TestEffort)

    def test__save_effort(self):
        """Test that :meth:`User._save_effort` saves an effort properly"""
        class TestRepository(UserRepository):
            def _save_location(self, cursor, location):
                location.id = 1

        class TestSaveEffortCursor(TestCursor):
            fields = {
                'start_time': 'test_st',
                'duration': 'test_d',
                'user': 2,
                'location': 1
            }

            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query,
                    'INSERT INTO efforts (start_time, duration, "user", location)'
                        ' VALUES (%s, %s, %s, %s)'
                )
                self.test_case.assertEqual(
                    params,
                    (
                        self.fields['start_time'],
                        self.fields['duration'],
                        self.fields['user'],
                        self.fields['location'],
                    )
                )

        class TestLocation(object):
            pass

        class TestEffort(object):
            start_time = TestSaveEffortCursor.fields['start_time']
            duration = TestSaveEffortCursor.fields['duration']
            location = TestLocation()

        class TestUser(object):
            id = TestSaveEffortCursor.fields['user']

        repository = TestRepository(TestConnection(TestCursor, self))
        repository._save_effort(TestSaveEffortCursor(self), TestEffort(), TestUser())

    def test__delete_effort(self):
        """Test that :meth:`UserRepository._delete_effort` deletes an effort"""
        class TestLocation(object):
            id = 1

        class TestUser(object):
            id = 5

        class TestEffort(object):
            start_time = 'test_st'
            duration = 'test_d'
            location = TestLocation()

        class TestDeleteEffortCursor(TestCursor):
            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query,
                    'DELETE FROM efforts WHERE '
                        'start_time = %s AND '
                        'duration = %s AND '
                        '"user" = %s AND '
                        'location = %s'
                )
                self.test_case.assertEqual(
                    params,
                    (
                        TestEffort.start_time,
                        TestEffort.duration,
                        TestEffort.location.id,
                        TestUser.id
                    )
                )

        repository = UserRepository(TestConnection(TestCursor, self))
        cursor = TestConnection(TestDeleteEffortCursor, self).cursor()
        repository._delete_effort(cursor, TestEffort(), TestUser())

    def test_save(self):
        """Test that :meth:`UserRepository.save` saves a user properly"""
        class TestEffort(object):
            pass

        class TestUser(object):
            username = 'username'
            first_name = 'first_name'
            last_name = 'last_name'
            email = 'email'
            efforts = [TestEffort()]

        class TestSaveCursor(TestCursor):
            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query,
                    'INSERT INTO users '
                        '(username, first_name, last_name, email) VALUES '
                        '(%s, %s, %s, %s) RETURNING id'
                )
                self.test_case.assertEqual(
                    params,
                    (
                        TestUser.username,
                        TestUser.first_name,
                        TestUser.last_name,
                        TestUser.email,
                    )
                )

            def fetchone(self):
                return {'id': 1}

        class TestRepository(UserRepository):
            user = TestUser()

            def _update(self, cursor, user):
                self.test_case.assertEqual(user, self.user)

            def _save_effort(self, cursor, effort, user):
                self.test_case.assertEqual(effort, TestUser.efforts[0])
                self.test_case.assertEqual(user, self.user)

        TestRepository.test_case = self

        repository = TestRepository(TestConnection(TestSaveCursor, self))
        repository.save(repository.user)
        repository.user.id = 1
        repository.save(repository.user)

    def test__update(self):
        """Test that :meth:`UserRepository._update` updates user data"""

        class TestUser(object):
            id = 1
            username = 'username'
            email = 'test@email'

            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name

        class TestEffort(object):
            def __init__(self, effort_id):
                self.id = effort_id

            def __eq__(self, other):
                return self.id == other.id

            def __ne__(self, other):
                return not self == other

            def __hash__(self):
                return self.id

        class TestRepository(UserRepository):
            existing = TestUser('first', 'last')
            new_user = TestUser('newfirst', 'newlast')

            def __init__(self, *args, **kwargs):
                super(TestRepository, self).__init__(*args, **kwargs)
                self.existing.efforts = set([TestEffort(1), TestEffort(2)])
                self.new_user.efforts = set([TestEffort(2), TestEffort(3)])

            def get(self, cursor, user_id=None):
                return self.existing

            def _save_effort(self, cursor, effort, user):
                self.test_case.assertEqual(effort, TestEffort(3))
                self.test_case.assertEqual(user, self.new_user)

            def _delete_effort(self, cursor, effort, user):
                self.test_case.assertEqual(effort, TestEffort(1))
                self.test_case.assertEqual(user, self.new_user)

        TestRepository.test_case = self

        class TestUpdateCursor(TestCursor):
            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    'UPDATE users SET first_name = %s, last_name = %s '
                        'WHERE id = %s',
                    query
                )
                self.test_case.assertEqual(params, ('newfirst', 'newlast', 1))

        repository = TestRepository(TestConnection(TestCursor, self))
        repository._update(TestUpdateCursor(self), repository.new_user)

    def test_delete(self):
        """Test that :meth:`UserRepository.delete` deletes a user from the
        repository.
        """
        class TestUser(object):
            id = 1

        class TestDeleteCursor(TestCursor):
            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query, 'DELETE FROM users WHERE id = %s'
                )
                self.test_case.assertEqual(params, (1,))

        class TestRepository(UserRepository):
            user = TestUser()

            def _delete_efforts(self, cursor, user):
                self.test_case.assertEqual(user, self.user)

        TestRepository.test_case = self

        repository = TestRepository(TestConnection(TestDeleteCursor, self))
        repository.delete(repository.user)

    def test_get(self):
        """Test that :meth:`UserRepository.get` returns a user properly"""

        class TestEffort(object):
            def __init__(self, effort_id):
                self.id = effort_id

            def __eq__(self, other):
                return self.id == other.id

            def __ne__(self, other):
                return not self == other

        class TestRepository(UserRepository):
            fields = {'id': 1, 'username': 'test_username'}
            effort = TestEffort(2)

            def _get(self, cursor, field, value):
                self.test_case.assertIn(field, ['username', 'id'])
                if field == 'username':
                    self.test_case.assertEqual(value, 'test_username')
                elif field == 'id':
                    self.test_case.assertEqual(value, 1)

                return [self.fields.copy()]

            def _get_efforts(self, cursor, user):
                return [self.effort]

        TestRepository.test_case = self

        class TestUser(object):
            def __init__(self, **kwargs):
                user_fields = TestRepository.fields.copy()
                del user_fields['id']

                self.test_case.assertEqual(user_fields, kwargs)
                for kw in kwargs:
                    setattr(self, kw, kwargs[kw])

            def add_effort(self, effort):
                self.test_case.assertEqual(effort, TestRepository.effort)

            def __eq__(self, other):
                return self.__dict__ == other.__dict__

            def __ne__(self, other):
                return not self == other

        TestUser.test_case = self
        import leaderboard.persistence.user as ur_module
        ur_module.User = TestUser

        user_fields = TestRepository.fields.copy()
        del user_fields['id']
        user = TestUser(**user_fields)
        user.id = 1

        repository = TestRepository(TestConnection(TestCursor, self))

        returned_user = repository.get(user_id=1)

        self.assertEqual(returned_user, user)
        self.assertTrue(hasattr(returned_user, 'id'))
        self.assertEqual(returned_user.id, 1)

        self.assertEqual(repository.get(username='test_username'), user)
        self.assertRaises(ValueError, repository.get, user_id=1, username='u')

    def test_set_team(self):
        """Test that :meth:`UserRepository.set_team` sets a user's team"""
        class TestTeam(object):
            id = 1

        class TestUser(object):
            id = 2

        class TestSetTeamCursor(TestCursor):
            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query, 'UPDATE users2teams SET team = %s WHERE "user" = %s'
                )
                self.test_case.assertEqual(params, (1, 2))

        repository = UserRepository(TestConnection(TestSetTeamCursor, self))
        repository.set_team(TestUser(), TestTeam())
        repository.set_team(TestUser(), 1)


class TeamRepositoryTestCase(unittest.TestCase):
    """Test :class:`leaderboard.persistence.TeamRepository`"""

    def test_get(self):
        """Test that :meth:`TestRepository.get` returns an initialized team"""
        class TestUser(object):
            def __init__(self, user_id):
                self.id = user_id

            def __eq__(self, other):
                return type(self) == type(other) and self.id == other.id

            def __ne__(self, other):
                return not self == other

        class TestTeam(object):
            id = 1

            def __init__(self, name):
                self.name = name
                self.members = []

            def add_user(self, user):
                self.members.append(user)

            def __eq__(self, other):
                return (
                    self.id == other.id and
                    self.name == other.name and
                    self.members == other.members
                )

            def __ne__(self, other):
                return not self == other

        import leaderboard.persistence.team as tr_module
        tr_module.Team = TestTeam

        class TestRepository(TeamRepository):
            def _get(self, cursor, field, value):
                self.test_case.assertIn(field, ['id', 'name'])
                if field == 'id':
                    self.test_case.assertEqual(value, 1)
                elif field == 'name':
                    self.test_case.assertEqual(value, 'name')
                return [{'id': 1, 'name': 'name'}]

            def _get_users(self, cursor, team):
                return [TestUser(1), TestUser(2)]

        TestRepository.test_case = self

        repository = TestRepository(TestConnection(TestCursor, self))
        team = TestTeam('name')
        team.members = [TestUser(1), TestUser(2)]

        returned_team = repository.get(team_id=1)

        self.assertEqual(returned_team, team)
        self.assertTrue(hasattr(returned_team, 'id'))
        self.assertEqual(returned_team.id, 1)

        self.assertEqual(repository.get(name='name'), team)
        self.assertRaises(ValueError, repository.get, team_id=1, name='name')

    def test_save(self):
        """Test that :meth:`TeamRepository.save` saves a user to the database"""
        class TestUser(object):
            def __init__(self, user_id):
                self.id = user_id

            def __eq__(self, other):
                return type(self) == type(other) and self.id == other.id

            def __ne__(self, other):
                return not self == other

        class TestTeam(object):
            name = 'name'
            users = [TestUser(1)]

            def __iter__(self):
                self.iter = iter(self.users)
                return self.iter

            def next(self):
                return self.iter.next()

        class TestSaveCursor(TestCursor):
            def execute(self, query, params=None):
                if query.startswith('INSERT'):
                    self.test_case.assertEqual(
                        query,
                        'INSERT INTO teams (name) VALUES (%s) RETURNING id'
                    )
                    self.test_case.assertEqual(params, ('name',))

            def fetchone(self):
                return {'id': 1}

        class TestUserRepository(object):
            def __init__(self, connection):
                pass

            def save(self, user):
                self.test_case.assertEqual(user, TestUser(1))

        TestUserRepository.test_case = self
        import leaderboard.persistence.team as tr_module
        tr_module.UserRepository = TestUserRepository

        class TestTeamRepository(TeamRepository):
            def _update(self, cursor, team):
                self.test_case.assertEqual(team.name, 'name')
                self.test_case.assertEqual(team.id, 1)

        TestTeamRepository.test_case = self

        team = TestTeam()
        repository = TestTeamRepository(TestConnection(TestSaveCursor, self))
        repository.save(team)
        team.id = 1
        repository.save(team)

    def test_delete(self):
        """Test that :meth:`TeamRepository.delete` deletes an empty team"""
        class TestUser(object):
            id = 1

        class TestTeam(object):
            id = 1

            def __init__(self, members):
                self.members = members

            def __len__(self):
                return len(self.members)

        class TestDeleteCursor(TestCursor):
            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query, 'DELETE FROM teams WHERE id = %s'
                )
                self.test_case.assertEqual(params, (1,))

        repository = TeamRepository(TestConnection(TestDeleteCursor, self))
        team = TestTeam([TestUser()])
        self.assertRaises(ConstraintError, repository.delete, team)

        team = TestTeam([])
        repository.delete(team)

    def test__update(self):
        """Test that :meth:`TeamRepository._update` updates an existing team"""
        class TestUser(object):
            def __init__(self, user_id):
                self.id = user_id

            def __eq__(self, other):
                return type(self) == type(other) and self.id == other.id

            def __ne__(self, other):
                return not self == other

            def __hash__(self):
                return self.id

        class TestTeam(object):
            id = 1

            def __init__(self, name, members=None):
                self.name = name
                self.members = members or []

            def __iter__(self):
                self.iter = iter(self.members)
                return self.iter

            def next(self):
                return self.iter.next()

        class TestUpdateCursor(TestCursor):
            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query, 'UPDATE teams SET name = %s WHERE id = %s'
                )
                self.test_case.assertEqual(params, ('name', 1))

        class TestTeamRepository(TeamRepository):
            team = TestTeam('old_name', [TestUser(1), TestUser(2)])
            def get(self, cursor, team_id=None):
                self.test_case.assertEqual(team_id, 1)
                return self.team

        TestTeamRepository.test_case = self

        class TestUserRepository(object):
            def __init__(self, connection):
                pass

            def save(self, user):
                self.test_case.assertEqual(user, TestUser(3))

            def set_team(self, user, team):
                self.test_case.assertEqual(team.id, 1)
                self.test_case.assertEqual(team.name, 'name')
                self.test_case.assertEqual(team.members, [TestUser(2), TestUser(3)])
                self.test_case.assertEqual(user, TestUser(3))

        TestUserRepository.test_case = self

        import leaderboard.persistence.team as tr_module
        tr_module.UserRepository = TestUserRepository

        repository = TestTeamRepository(TestConnection(TestUpdateCursor, self))
        repository._update(TestUpdateCursor(self), TestTeam('name', [TestUser(2), TestUser(3)]))

    def test__get_users(self):
        """Test that :meth:`TeamRepository._get_users` returns the users
        associated with a team
        """
        class TestTeam(object):
            id = 1

        class TestUser(object):
            id = 2

        class TestGetUsersCursor(TestCursor):
            def execute(self, query, params=None):
                self.test_case.assertEqual(
                    query, 'SELECT "user" FROM users2teams WHERE team = %s'
                )
                self.test_case.assertEqual(params, (1,))

            def fetchall(self):
                return [{'user': 2}]

        class TestUserRepository(object):
            users2teams_table_name = 'users2teams'

            def __init__(self, connection):
                pass

            def get(self, user_id=None):
                self.test_case.assertEqual(user_id, 2)

        TestUserRepository.test_case = self

        import leaderboard.persistence.team as tr_module
        tr_module.UserRepository = TestUserRepository

        repository = TeamRepository(TestConnection(TestGetUsersCursor, self))
        users = [u for u in 
                    repository._get_users(TestGetUsersCursor(self), TestTeam())
                ]


class TestRepository(Repository):
    table_name = 'test'

    def _create(self, cursor, row):
        return row


class TestConnection(object):
    """Mock :class:`connection`"""

    def __init__(self, cursor, test_case):
        self.Cursor = cursor
        self.test_case = test_case

    def commit(self):
        pass

    def cursor(self, cursor_factory=None):
        """Return a mock database cursor"""
        return self.Cursor(self.test_case)


class TestCursor(object):
    """Mock :class:`cursor`"""

    def __init__(self, test_case):
        self.test_case = test_case

    def close(self):
        pass

    def execute(self, query, params=None):
        """Mock a query execution

        :param query: the query string to run
        :param params: a :class:`tuple` of query parameters
        """
        pass

    def fetchall(self):
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
