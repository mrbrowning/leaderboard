"""
    leaderboard.endpoints
    ======================

    Implements the endpoints for the leaderboard REST API.

    :author: Michael Browning
"""

from datetime import datetime, timedelta
from functools import wraps

from flask import request, abort, redirect

from leaderboard import app
import actions
from exceptions import HHException
from .helpers import view, render_json, DATETIME_FORMAT


def endpoint(fn):
    """Since the action layer nicely packages the error handling, we can
    standardize how the endpoints pass error messages through with this
    decorator.

    :param fn: the function to wrap
    """
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HHException as e:
            return _error_response(e.message)
        except Exception:
            return _error_response()

    return wrapped


@view(app, '/users', render_json, methods=['POST'])
@endpoint
def add_user():
    """Add a new HH user."""
    user_id = actions.add_user(
        request.json['username'],
        request.json['first_name'],
        request.json['last_name'],
        request.json['email'],
        int(request.json['team'])
    )

    response = _success_response()
    response['id'] = user_id

    return response


@view(app, '/teams', render_json, methods=['POST'])
@endpoint
def add_team():
    """Add a new HH team."""
    team_id = actions.add_team(request.json['name'])

    response = _success_response()
    response['id'] = team_id

    return response


@view(app, '/users/<int:user_id>', render_json, methods=['POST'])
@endpoint
def add_entry(user_id):
    """Add a new volunteer entry for the given user.

    :param user_id: the integer id of the user
    """
    actions.add_entry(
        datetime.strptime(request.json['start_time'], DATETIME_FORMAT),
        timedelta(0, int(request.json['duration'])),
        int(request.json['user']),
        float(request.json['latitude']),
        float(request.json['longitude'])
    )

    return _success_response()


@view(app, '/users/<int:user_id>', render_json, methods=['GET'])
@endpoint
def get_user(user_id):
    """Get a user's profile information.

    :param user_id: the integer id of the user
    """
    return actions.get_user(user_id).to_dict()


@view(app, '/users/best', render_json, methods=['GET'])
@endpoint
def get_best_users():
    """Get a listing of the top volunteers."""
    users = actions.get_users()
    user_data = []
    for u in users:
        if u.efforts:
            effort = int(reduce(
                lambda x, y: x + y, [e.duration for e in u.efforts]
            ).total_seconds())
        else:
            effort = 0

        team = actions.get_user_team(u)

        user_data.append({
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'effort': effort,
            'team': team.name,
        })

    num_users = int(request.args.get('num_users', len(user_data)))

    return {
        'users': sorted(
            user_data, key=lambda x: x['effort'], reverse=True
        )[:num_users],
    }


@view(app, '/teams', render_json, methods=['GET'])
@endpoint
def get_teams():
    """Get a listing of all the teams."""
    return {'teams': [t.to_dict() for t in actions.get_teams()]}


@view(app, '/teams/<int:team_id>', render_json, methods=['GET'])
@endpoint
def get_team(team_id):
    """Get a particular team's information.

    :param team_id: the integer id of the team
    """
    return actions.get_team(team_id).to_dict()


@view(app, '/teams/best', render_json, methods=['GET'])
def get_best_teams():
    """Get a listing of the top teams."""
    teams = actions.get_teams()
    team_data = []
    for t in teams:
        efforts = []
        for u in t.members:
            efforts.extend([e.duration for e in t.members[u].efforts])

        if efforts:
            effort = int(reduce(lambda x, y: x + y, efforts).total_seconds())
        else:
            effort = 0

        team_data.append({'id': t.id, 'name': t.name, 'effort': effort})

    num_teams = int(request.args.get('num_teams', len(team_data)))

    return {
        'teams': sorted(
            team_data, key=lambda x: x['effort'], reverse=True
        )[:num_teams],
    }


def _error_response(message='error'):
    """Default error response.

    :param message: the error message to include in the response
    """
    return {
        'error': True,
        'time': datetime.strftime(datetime.now(), DATETIME_FORMAT),
        'message': message,
    }


def _success_response():
    """Default success response for endpoints that don't return a value."""
    return {
        'error': False,
        'time': datetime.strftime(datetime.now(), DATETIME_FORMAT),
    }
