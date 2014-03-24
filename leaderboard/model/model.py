"""
    leaderboard.model.model
    ========================

    Implements the base classes for entity and value types.

    :author: Michael Browning
"""

from ..exceptions import MissingFieldError, DefinitionError


class Model(object):
    """The base domain model class."""

    def __init__(self, **kwargs):
        self._validate(**kwargs)

    def _validate(self, **kwargs):
        """Apply the validation rules to each of the input fields and store"""
        for kw in self._validation_rules:
            if kw not in kwargs:
                raise MissingFieldError(type(self).__name__, kw)

        for kw in kwargs:
            if kw not in self._validation_rules:
                raise DefinitionError(type(self).__name__, kw)

            rule = self._validation_rules[kw]
            setattr(self, kw, rule(kwargs[kw]))

    def to_dict(self):
        return {kw: getattr(self, kw) for kw in self._validation_rules}


class Entity(Model):
    """The base entity class."""
    pass


class Value(Model):
    """The base, immutable value class."""

    def __init__(self, **kwargs):
        super(Value, self).__init__(**kwargs)
        self._set = True

    def __setattr__(self, name, value):
        # This lets us initialize values in __init__, but then prevents further
        # modification.
        if name != 'id' and hasattr(self, '_set') and self._set:
            # Objects only receive an id when they're saved, so we need to allow
            # id assignment after creation.
            raise TypeError(
                'Type "%s" does not support attribute assignment' % (
                    type(self).__name__
                )
            )
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        # The last step in making a truly immutable object, to prevent self._set
        # from being deleted and thereby making attribute assignment possible
        # again.
        raise TypeError(
            'Type "%s" does not support attribute deletion' % (
                type(self).__name__
            )
        )

    def __eq__(self, other):
        if other:
            if isinstance(other, type(self)) or isinstance(self, type(other)):
                # We don't consider the object id in equality comparisons, since
                # it's metadata.
                self_dict = self.__dict__.copy()
                self_dict.pop('id', None)
                other_dict = other.__dict__.copy()
                other_dict.pop('id', None)

                return self_dict == other_dict
            else:
                return False
        else:
            return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        dict = self.__dict__.copy()
        dict.pop('id', None)
        return hash(
           tuple([(k, getattr(self, k)) for k in sorted(dict)])
        )
