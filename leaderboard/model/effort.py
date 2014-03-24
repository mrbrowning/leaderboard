"""
    leaderboard.model.effort
    =========================

    Implements the value object :class:`leaderboard.model.Effort`. This is a
    member of the :class:`User` aggregate.

    :author: Michael Browning
"""

from datetime import datetime, timedelta

from .model import Value
from .location import Location
from . import type_validator
from ..exceptions import ValidationError
from ..helpers import DATETIME_FORMAT


def threshold_validator(threshold):
    """Returns a validator function that checks whether a supplied value is
    of the same type and greater than the value represented by the given
    threshold object.

    :param threshold: the threshold object
    """
    def validator(obj):
        try:
            valid = obj > threshold
        except TypeError:
            raise ValidationError('type %s is not %s' % (type(obj), type(threshold)))

        if valid:
            return obj
        else:
            raise ValidationError()

    return validator


class Effort(Value):
    """A completed volunteer opportunity, containing information about when and
    where it happened and for how long."""

    _validation_rules = {
        'start_time': threshold_validator(datetime.fromtimestamp(0)),
        'duration': threshold_validator(timedelta(0)),
        'location': type_validator(Location),
    }

    def overlaps(self, other):
        """Return `True` if the supplied effort overlaps in time with this one.

        :param other: an object of type :class:`Effort`
        """
        if self.start_time == other.start_time:
            return True

        end = self.start_time + self.duration
        return (
            self.start_time < other.start_time < end or
            self.start_time < other.start_time + other.duration < end
        )

    def to_dict(self):
        effort_dict = super(Effort, self).to_dict()
        effort_dict['start_time'] = (
            datetime.strftime(effort_dict['start_time'], DATETIME_FORMAT)
        )
        effort_dict['duration'] = int(effort_dict['duration'].total_seconds())
        effort_dict['location'] = effort_dict['location'].to_dict()

        return effort_dict

    @staticmethod
    def create_effort(**kwargs):
        """Return an instantiated :class:`Effort` object"""
        if 'location' in kwargs:
            location = kwargs['location']
        elif 'latitude' in kwargs and 'longitude' in kwargs:
            location = Location(
                latitude=kwargs['latitude'], longitude=kwargs['longitude']
            )

        return Effort(
            start_time=kwargs['start_time'],
            duration=kwargs['duration'],
            location=location
        )
