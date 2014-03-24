"""
    leaderboard.model.user
    =======================

    Implements the :class:`User` entity. :class:`User` is the root of its own
    aggregate, which also contains the :class:`Effort` and :class:`Location`
    types.

    :author: Michael Browning
"""

from .model import Entity
from .effort import Effort
from . import re_validator, type_validator
from ..exceptions import ConstraintError

name_transform = lambda x: x[0].upper() + x[1:]


class User(Entity):
    """A user."""

    _validation_rules = {
        'username': re_validator(r'^[A-z][A-z0-9]+$'),
        'first_name': re_validator(r'^[A-z]+$', name_transform),
        'last_name': re_validator(r'^[A-z]+$', name_transform),
        'email': re_validator(r'^[^@]+@[^@]+$'),
    }

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.efforts = set()

    def full_name(self):
        """The user's full first and last name."""
        return '%s %s' % (first_name, last_name)

    def time_worked(self):
        """The total time put in volunteering by this user, expressed in
        seconds.
        """
        total = sum(e.duration.total_seconds() for e in self.efforts)

    def add_effort(self, *args, **kwargs):
        """Add an effort to this user's record. Efforts may not overlap in time.
        """
        if args:
            # The calling context is a repository, and since saved efforts are
            # guaranteed to have no overlap we don't need to validate them.
            effort = args[0]
        else:
            effort = Effort.create_effort(**kwargs)

            for e in self.efforts:
                if effort.overlaps(e):
                    raise ConstraintError('Efforts may not overlap in time')

        self.efforts.add(effort)

    def to_dict(self):
        user_dict = super(User, self).to_dict()
        user_dict['efforts'] = [e.to_dict() for e in self.efforts]

        return user_dict
