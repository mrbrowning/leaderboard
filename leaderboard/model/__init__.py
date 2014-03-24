"""
    leaderboard.model
    ==================

    Implements the domain model.

    :author: Michael Browning
"""

import re

from ..exceptions import ValidationError


def re_validator(pattern, transform=None):
    """Returns a validator function for domain objects that checks a string
    against the supplied regular expression and returns that string with a
    transformation applied if it passes.

    :param pattern: a string representing a regular expression
    :param transform: a callable taking a single argument and returning another
                      value of that type
    """
    pattern = re.compile(pattern)

    def validator(value):
        if pattern.match(value):
            return transform(value) if transform else value
        else:
            raise ValidationError()

    return validator


def type_validator(field_type):
    """Returns a validator function for domain objects that checks whether its
    input is of the supplied type.

    :param field_type: the desired type of the field being validated
    """
    def validator(value):
        if isinstance(value, field_type):
            return value
        else:
            raise ValidationError()

    return validator


from .team import Team
from .user import User
