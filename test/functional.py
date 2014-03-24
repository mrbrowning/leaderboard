"""
    test.functional
    ===============

    Test app functionality from user perspective.

    :author: Michael Browning
"""

import unittest
import os
import subprocess
import json
import time

import leaderboard
from leaderboard import app, get_connection

PSQL_ROOT = '/Applications/Postgres.app/Contents/MacOS/bin'


class FunctionalTestCase(unittest.TestCase):
    """Test app functionality from user perspective."""

    def setUp(self):
        # We have to close our global connection so that dropdb will work.
        leaderboard.connection.close()

        DEVNULL = open(os.devnull, 'wb')
        with open('test/schema') as f:
            dbp = subprocess.call(
                ['%s/psql' % PSQL_ROOT],
                stdin=f,
                stderr=DEVNULL,
                stdout=DEVNULL
            )
        DEVNULL.close()

        # Now we reopen it so that the repositories can use it again.
        leaderboard.connection = get_connection()

        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_get_teams(self):
        """Test /teams endpoint"""
        data = json.loads(self.app.get('/teams').data)

        self.assertIn('teams', data)
        self.assertEquals(len(data['teams']), 3)

    def test_get_team(self):
        """Test /teams/<int> endpoint"""
        team_id = 1
        data = json.loads(self.app.get('/teams/%i' % team_id).data)

        self.assertIn('name', data)
        self.assertIn('members', data)

    def test_get_user(self):
        """Test /users/<int> GET endpoint"""
        user_id = 3
        data = json.loads(self.app.get('/users/%i' % user_id).data)

        for field in ('username', 'first_name', 'last_name', 'email', 'efforts'):
            self.assertIn(field, data)

    def test_add_entry(self):
        """Test /users/<int> POST endpoint"""
        from datetime import datetime
        from leaderboard.helpers import DATETIME_FORMAT

        user_id = 3
        post_data = {
            'start_time': datetime.strftime(datetime.now(), DATETIME_FORMAT),
            'duration': 1000,
            'user': user_id,
            'latitude': 41.5,
            'longitude': 71.5,
        }

        self.app.post(
            '/users/%i' % user_id,
            content_type='application/json',
            data=json.dumps(post_data)
        )

        data = json.loads(self.app.get('/users/%i' % user_id).data)

        location = {k: post_data[k] for k in (u'latitude', u'longitude')}
        effort = {
            unicode(k): unicode(post_data[k])
            if type(post_data[k]) is str else post_data[k]
            for k in post_data if k not in ('latitude', 'longitude')
        }
        effort[u'location'] = location
        del effort[u'user']

        self.assertEqual(len(data['efforts']), 1)
        self.assertEqual(list(data['efforts'])[0], effort)

    def test_add_user(self):
        """Test /users POST endpoint"""
        post_data = {
            'username': 'rmonkey',
            'first_name': 'Robert',
            'last_name': 'Monkey',
            'email': 'rmonkey@monkeys.com',
            'team': 1,
        }

        data = json.loads(self.app.post(
            '/users',
            content_type='application/json',
            data=json.dumps(post_data)
        ).data)

        self.assertIn('id', data)

        del post_data['team']
        user = {unicode(k): unicode(post_data[k]) for k in post_data}
        user[u'efforts'] = []
        user_data = json.loads(self.app.get('/users/%i' % data['id']).data)

        self.assertEqual(user_data, user)

    def test_add_team(self):
        """Test /teams POST endpoint"""
        post_data = {u'name': u'Dweeblezorks'}

        data = json.loads(self.app.post(
            '/teams',
            content_type='application/json',
            data=json.dumps(post_data)
        ).data)

        self.assertIn('id', data)
        team_data = json.loads(self.app.get('/teams/%i' % data['id']).data)
        post_data['members'] = []
        self.assertEqual(team_data, post_data)

    def test_best_teams(self):
        """Test /teams/best endpoint"""
        from datetime import datetime
        from leaderboard.helpers import DATETIME_FORMAT

        user_id = 3
        post_data = {
            'start_time': datetime.strftime(datetime.now(), DATETIME_FORMAT),
            'duration': 1000,
            'user': user_id,
            'latitude': 41.5,
            'longitude': 71.5,
        }

        self.app.post(
            '/users/%i' % user_id,
            content_type='application/json',
            data=json.dumps(post_data)
        )

        data = json.loads(self.app.get('/teams/best?num_teams=2').data)

        self.assertEqual(len(data['teams']), 2)
        self.assertEqual(data['teams'][0]['name'], 'Red Team')

    def test_best_users(self):
        """Test /users/best endpoint"""
        from datetime import datetime
        from leaderboard.helpers import DATETIME_FORMAT

        user_id = 3
        post_data = {
            'start_time': datetime.strftime(datetime.now(), DATETIME_FORMAT),
            'duration': 1000,
            'user': user_id,
            'latitude': 41.5,
            'longitude': 71.5,
        }

        self.app.post(
            '/users/%i' % user_id,
            content_type='application/json',
            data=json.dumps(post_data)
        )

        data = json.loads(self.app.get('/users/best?num_users=2').data)

        self.assertEqual(len(data['users']), 2)
        self.assertEqual(data['users'][0]['username'], 'mbrowning')


if __name__ == '__main__':
    unittest.main(verbosity=2)
