"""
    leaderboard.exceptions
    =======================

    leaderboard-specific exceptions.

    :author: Michael Browning
"""


class HHException(Exception):
    """The base exception class for leaderboard errors."""
    pass


class DefinitionError(HHException):
    """Error for when domain objects initiated with non-existent field."""

    def __init__(self, cls_name, field):
        super(DefinitionError, self).__init__(
            'Class %s has no field %s' % (cls_name, field)
        )


class ConstraintError(HHException):
    """Error for when an operation on an object violates a model constraint."""
    pass


class MissingFieldError(HHException):
    """Error for when domain objects initiated with missing field."""

    def __init__(self, cls_name, field):
        super(MissingFieldError, self).__init__(
            'Class %s requires field %s' % (cls_name, field)
        )


class ValidationError(HHException):
    """Error for when a supplied domain field value fails to validate."""
    pass
