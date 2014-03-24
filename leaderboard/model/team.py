"""
    leaderboard.model.team
    =======================

    Implements the :class:`Team` entity.

    :author: Michael Browning
"""

from .model import Entity
from . import re_validator
from ..exceptions import ConstraintError


class Team(Entity):
    """A team."""

    _validation_rules = {
        'name': re_validator(r'[A-z][A-z0-9]'),
    }

    def __init__(self, **kwargs):
        super(Team, self).__init__(**kwargs)
        self.members = {}

    def time_worked(self):
        """The total time put in volunteering by all users on this team."""
        return sum(m.time_worked() for m in self.members)

    def add_user(self, user):
        """Add a user to this team. No two users may have the same username.

        :param user: An object of type :class:`User`
        """
        if user.username in self.members:
            raise ConstraintError(
                'Team %s has user with username %s' % (self.name, user.username)
            )
        self.members[user.username] = user

    def to_dict(self):
        team_dict = super(Team, self).to_dict()
        team_dict['members'] = [m.to_dict() for m in self.members.values()]

        return team_dict

    def __iter__(self):
        return iter(self.members.values())

    def __contains__(self, user):
        return user.username in self.members

    def __len__(self):
        return len(self.members)
