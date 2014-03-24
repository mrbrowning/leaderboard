"""
    test.model
    ==========

    Test domain model and helpers.

    :author: Michael Browning
"""

import unittest
from datetime import datetime, timedelta

from leaderboard.model import User, Team, re_validator, type_validator
from leaderboard.model.model import Model, Value
from leaderboard.model.effort import Effort
from leaderboard.model.location import Location
from leaderboard.exceptions import ValidationError, MissingFieldError, \
    DefinitionError, ConstraintError


class ReValidatorTest(unittest.TestCase):
    """Test :func:`leaderboard.model.re_validator`"""

    def setUp(self):
        self.re = r'[A-Z]+'
        self.transform = lambda x: x.lower()
        self.validator = re_validator(self.re)
        self.value = 'TEST'

    def test_re_validator_passes_good_input(self):
        """Test :func:`re_validator` returns good input as-is"""
        self.assertEqual(self.validator(self.value), self.value)

    def test_re_validator_transforms_input(self):
        """Test :func:`re_validator` applies transformation to good input"""
        validator = re_validator(self.re, self.transform)
        self.assertEqual(validator(self.value), self.transform(self.value))

    def test_re_validator_fails_bad_input(self):
        """Test :func:`re_validator` raises :class:`ValidationError` on bad
        input
        """
        self.assertRaises(ValidationError, self.validator, self.value.lower())


class TypeValidatorTest(unittest.TestCase):
    """Test :func:`leaderboard.model.type_validator`"""

    def setUp(self):
        self.obj = [1, 2, 3]
        self.validator = type_validator(list)

    def test_type_validator_passes_good_input(self):
        """Test :func:`type_validator` returns good input as-is"""
        self.assertEqual(self.validator(self.obj), self.obj)

    def test_type_validator_fails_bad_input(self):
        """Test :func:`type_validator` raises :class:`ValidationError on bad
        input
        """
        self.assertRaises(ValidationError, self.validator, ())


class ModelTest(unittest.TestCase):
    """Test :class:`leaderboard.model.model.Model`"""

    def setUp(self):
        class TestClass(Model):
            _validation_rules = {
                'field': lambda x: x
            }
        self.TestClass = TestClass
        self.fields = {'field': 'value'}

    def test_initializes_with_fields(self):
        """Test that :class:`Model` allows initialization when all proper fields
        are included
        """
        test_model = self.TestClass(**self.fields)
        self.assertEqual(
            self.fields, {k: getattr(test_model, k) for k in self.fields.keys()}
        )

    def test_missing_fields_fails(self):
        """Test that :class:`User` doesn't allow initialization with fields
        missing
        """
        self.assertRaises(MissingFieldError, self.TestClass)

    def test_extra_fields_fails(self):
        """Test that :class:`User` doesn't allow initialization with extra
        fields passed
        """
        self.fields['extra'] = 'extra'
        self.assertRaises(DefinitionError, self.TestClass, **self.fields)


class ValueTest(unittest.TestCase):
    """Test :class:`leaderboard.model.model.Value`"""

    def setUp(self):
        class TestClass(Value):
            _validation_rules = {'field': lambda x: x}

        self.TestClass = TestClass
        self.fields = {'field': 'value'}

    def test_initializes(self):
        """Test that :class:`Value` can be initialized properly"""
        test_value = self.TestClass(**self.fields)
        self.assertEqual(
            self.fields, {k: getattr(test_value, k) for k in self.fields.keys()}
        )

    def test_no_attribute_setting(self):
        """Test that :class:`Value` prevents attributes from being set"""
        test_value = self.TestClass(**self.fields)
        self.assertRaises(TypeError, setattr, test_value, 'field', 'new_value')

    def test_no_attribute_deletion(self):
        """Test that :class:`Value` prevents attributes from being deleted"""
        test_value = self.TestClass(**self.fields)
        self.assertRaises(TypeError, delattr, test_value, 'field')

    def test_can_assign_id(self):
        """Test that :class:`Value` allows an `id` attribute to be set"""
        test_value = self.TestClass(**self.fields)
        test_id = 5
        test_value.id = test_id

        self.assertEqual(test_value.id, test_id)

    def test_equality_by_data(self):
        """Test that :class:`Value` tests equality by data, not identity"""
        fields2 = self.fields.copy()
        test_value1 = self.TestClass(**self.fields)
        test_value2 = self.TestClass(**fields2)

        self.assertEqual(test_value1, test_value2)

        fields3 = self.fields.copy()
        fields3['field'] = 'different'
        test_value3 = self.TestClass(**fields3)

        self.assertNotEqual(test_value1, test_value3)

    def test_equal_with_different_ids(self):
        """Test that :class:`Value` objects compare equal with different ids"""
        fields2 = self.fields.copy()
        test_value1 = self.TestClass(**self.fields)
        test_value2 = self.TestClass(**fields2)
        test_value1.id = 5

        self.assertEqual(test_value1, test_value2)

        test_value2.id = 10
        self.assertEqual(test_value1, test_value2)

    def test_different_types_not_equal(self):
        """Test that :class:`Value` objects don't compare equal if they have the
        same attributes but different types
        """
        class DTTestClass(Value):
            _validation_rules = {'field': lambda x: x}

        test_value1 = self.TestClass(**self.fields)
        test_value2 = DTTestClass(**self.fields.copy())
        self.assertNotEqual(test_value1, test_value2)


class UserTest(unittest.TestCase):
    """Test :class:`leaderboard.model.User`"""

    def setUp(self):
        self.fields = {
            'username': 'ttakemitsu',
            'first_name': 'Toru',
            'last_name': 'Takemitsu',
            'email': 'ttakemitsu@gmail.com',
        }
    
    def test_user_initializes(self):
        """Test that :class:`User` initializes when fields are valid"""
        user = User(**self.fields)
        self.assertEqual(
            self.fields,
            {k: getattr(user, k) for k in self.fields.keys()}
        )

    def test_username_field_starts_with_letter(self):
        """Test that :class:`User` requires the username to be non-empty and to
        start with a letter and only be alphanumeric otherwise
        """
        self.fields['first_name'] = ''
        self.assertRaises(ValidationError, User, **self.fields)

        self.fields['username'] = '9Test'
        self.assertRaises(ValidationError, User, **self.fields)

        self.fields['username'] = 'Test!'
        self.assertRaises(ValidationError, User, **self.fields)

    def test_first_name_fields_accepts_only_letters(self):
        """Test that :class:`User` requires first_name to be non-empty and
        consist only of letters
        """
        self.fields['first_name'] = ''
        self.assertRaises(ValidationError, User, **self.fields)

        self.fields['first_name'] = 'F9'
        self.assertRaises(ValidationError, User, **self.fields)

    def test_last_name_fields_accepts_only_letters(self):
        """Test that :class:`User` requires last_name to be non-empty and
        consist only of letters
        """
        self.fields['last_name'] = ''
        self.assertRaises(ValidationError, User, **self.fields)

        self.fields['last_name'] = 'F9'
        self.assertRaises(ValidationError, User, **self.fields)

    def test_proper_names_transformed(self):
        """Test that :class:`User` transforms proper names correctly"""
        test_fields = self.fields.copy()
        test_fields['first_name'] = test_fields['first_name'].lower()
        test_fields['last_name'] = (
            test_fields['last_name'][0].lower() +
            test_fields['last_name'][1:].upper()
        )
        user = User(**self.fields)

        self.assertEqual(
            self.fields,
            {k: getattr(user, k) for k in self.fields.keys()}
        )

    def test_add_effort_creates_effort(self):
        """Test that :meth:`User.add_effort` initializes and stores an object of
        type :class:`Effort`
        """
        fields = {
            'start_time': datetime.now(),
            'duration': timedelta(100),
            'latitude': 41.5,
            'longitude': 73.5,
        }

        user = User(**self.fields)
        location = Location(
            latitude=fields['latitude'], longitude=fields['longitude']
        )
        effort = Effort(
            start_time=fields['start_time'],
            duration=fields['duration'],
            location=location
        )

        user.add_effort(**fields)

        self.assertIn(effort, user.efforts)

    def test_add_effort_prevents_overlaps(self):
        """Test that :meth:`User.add_effort prevents the insertion of
        overlapping efforts in time."""
        fields = {
            'start_time': datetime.now(),
            'duration': timedelta(100),
            'latitude': 41.5,
            'longitude': 73.5,
        }

        user = User(**self.fields)
        user.add_effort(**fields)
        start_time = fields['start_time'] + timedelta(50)

        self.assertRaises(ConstraintError, user.add_effort, **fields)


class TeamTest(unittest.TestCase):
    """Test :class:`leaderboard.model.Team`"""

    def setUp(self):
        self.fields = {'name': 'Team'}

    def test_team_initializes(self):
        """Test that :class:`Team` initializes when fields are valid"""
        team = Team(**self.fields)
        self.assertEqual(
            self.fields, {k: getattr(team, k) for k in self.fields.keys()}
        )

    def test_add_user_adds_user(self):
        """Test that :meth:`Team.add_user` stores a supplied :class:`User`"""
        team = Team(**self.fields)

        fields = {
            'username': 'ttakemitsu',
            'first_name': 'Toru',
            'last_name': 'Takemitsu',
            'email': 'ttakemitsu@gmail.com',
        }
        user = User(**fields)
        team.add_user(user)
        self.assertIn(user, team)
        self.assertEqual(len(team), 1)

    def test_add_user_prevents_duplicate_usernames(self):
        """Test that :meth:`Team.add_user` prevents two users with the same
        username being on the team
        """
        team = Team(**self.fields)

        fields = {
            'username': 'ttakemitsu',
            'first_name': 'Toru',
            'last_name': 'Takemitsu',
            'email': 'ttakemitsu@gmail.com',
        }
        user = User(**fields)
        team.add_user(user)
        user2 = User(**fields.copy())
        self.assertRaises(ConstraintError, team.add_user, user2)


class EffortTest(unittest.TestCase):
    """Test :class:`leaderboard.model.effort.Effort`"""

    def setUp(self):
        class MockLocation(Location):
            _validation_rules = {}

        self.fields = {
            'start_time': datetime.now(),
            'duration': timedelta(100),
            'location': MockLocation(),
        }

    def test_effort_initializes(self):
        """Test that :class:`Effort` initializes when fields are valid"""
        effort = Effort(**self.fields)
        self.assertEqual(
            self.fields, {k: getattr(effort, k) for k in self.fields.keys()}
        )

    def test_start_time_later_than_epoch(self):
        """Test that :class:`Effort` requires the start time to be of type
        :class:`datetime` and later than the UNIX epoch
        """
        self.fields['start_time'] = '1960-01-01T12:00:00'
        self.assertRaises(ValidationError, Effort, **self.fields)

        self.fields['start_time'] = datetime(1960, 1, 1)
        self.assertRaises(ValidationError, Effort, **self.fields)

    def test_duration_greater_than_zero(self):
        """Test that :class:`Effort` requires the duration to be of type
        :class:`timedelta` and greater than zero
        """
        self.fields['duration'] = 0
        self.assertRaises(ValidationError, Effort, **self.fields)

        self.fields['duration'] = timedelta(0)
        self.assertRaises(ValidationError, Effort, **self.fields)

    def test_create_effort(self):
        """Test that :meth:`Effort.create_effort` properly initializes an object
        of type :class:`Effort`
        """
        fields = self.fields.copy()
        del fields['location']
        fields['latitude'] = 41.5
        fields['longitude'] = 63.5

        location = Location(
            latitude=fields['latitude'], longitude=fields['longitude']
        )
        self.fields['location'] = location

        effort = Effort.create_effort(**fields)

        self.assertEqual(
            self.fields, {k: getattr(effort, k) for k in self.fields.keys()}
        )


class LocationTest(unittest.TestCase):
    """Test :class:`leaderboard.model.location.Location`"""

    def setUp(self):
        self.fields = {'latitude': 41.5, 'longitude': 73.5}

    def test_location_initializes(self):
        """Test that :class:`Location` initializes when fields are valid"""
        location = Location(**self.fields)
        self.assertEqual(
            self.fields, {k: getattr(location, k) for k in self.fields.keys()}
        )

    def test_latitude_accepts_only_floats(self):
        """Test that :class:`Location` only allows float-parsable values in the
        latitude field
        """
        self.fields['latitude'] = '41.fail'
        self.assertRaises(ValidationError, Location, **self.fields)

    def test_longitude_accepts_only_floats(self):
        """Test that :class:`Location` only allows float-parsable values in the
        longitude field
        """
        self.fields['longitude'] = '41.fail'
        self.assertRaises(ValidationError, Location, **self.fields)


if __name__ == '__main__':
    unittest.main(verbosity=2)
