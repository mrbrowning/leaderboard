"""
    leaderboard.helpers
    ====================

    Implements helper functions.

    :author: Michael Browning
"""

from functools import wraps
import json

import flask
from werkzeug import BaseResponse

from .exceptions import ValidationError

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


def render_json(obj):
    """Returns a JSON-serialized representation of an object.

    :param obj: the object to serialize as JSON
    """
    try:
        return flask.jsonify(obj)
    except ValueError as e:
        # It's a list, which flask won't jsonify.
        response = flask.make_response(json.dumps(obj))
        response.headers['Content-Type'] = 'application/json'
        return response


def view(app, url, renderer, *args, **kwargs):
    """Substitute for :meth:`flask.Flask.route` which allows for the plugging in
    of different rendering adapters. Returns a decorator which isn't cumulative;
    i.e., you can apply multiple routes to a callable with :func:`view` and they
    will each apply to the callable's original output.

    :param app: a :class:`flask.Flask` app instance
    :param url: the url to route to
    :param renderer: a callable that returns the rendered output; if None,
                     returns the wrapped function's original output
    """
    defaults = kwargs.pop('defaults', {})
    route_id = object()
    defaults['_route_id'] = route_id

    def decorator(fn):
        @app.route(url, defaults=defaults, *args, **kwargs)
        @wraps(fn)
        def wrapper(*args, **kwargs):
            this_route = kwargs.get('_route_id')
            if not getattr(fn, 'is_route', False):
                del kwargs['_route_id']

            result = fn(*args, **kwargs)

            # This lets us pass the output of a callable that's already been
            # wrapped and routed to a different route straight through.
            if this_route is not route_id:
                return result
            # result is a redirect
            if isinstance(result, (app.response_class, BaseResponse)):
                return result
            if renderer is None:
                return result

            return renderer(result)

        wrapper.is_route = True
        return wrapper

    return decorator
