"""
    leaderboard.model.location
    ===========================

    Implements the value object :class:`Location`.

    :author: Michael Browning
"""

from .model import Value
from ..exceptions import ValidationError


def cast_validator(caster):
    """Returns a validation function for fields that just need to be cast to a
    particular type.

    :param caster: the casting callable
    """
    def validator(value):
        try:
            return caster(value)
        except ValueError:
            raise ValidationError()

    return validator


class Location(Value):
    """A physical location expressed as latitude/longitude."""

    _validation_rules = {
        'latitude': cast_validator(float),
        'longitude': cast_validator(float),
    }
