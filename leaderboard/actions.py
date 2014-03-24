"""
    leaderboard.actions
    ====================

    Implements the actions for the leaderboard REST API.

    :author: Michael Browning
"""

from datetime import datetime

from leaderboard.model import User, Team
from leaderboard.persistence import UserRepository, TeamRepository


def add_user(username, first_name, last_name, email, team_id):
    """Add a new user to a given team.

    :param first_name: the user's first name
    :param last_name: the user's last name
    :param username: the user's unique username
    :param email: the user's email
    :param team_id: the user's integer team id
    """
    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email
    )

    user_repository = UserRepository()
    user_repository.save(user)
    user_repository.set_team(user, team_id)

    return user.id


def add_team(name):
    """Add a new team.

    :param name: the team name
    """
    team = Team(name=name)
    TeamRepository().save(team)

    return team.id


def add_entry(start_time, duration, user_id, latitude, longitude):
    """Add a new volunteer entry for a given user.

    :param start_time: the start time of the work done
    :param duration: how long the user worked
    :param user_id: the integer id of the user
    :param latitude: the latitude where the work was done
    :param longitude: the longitude where the work was done
    """
    user_repository = UserRepository()
    user = user_repository.get(user_id=user_id)
    user.add_effort(
        start_time=start_time,
        duration=duration,
        latitude=latitude,
        longitude=longitude
    )
    user_repository.save(user)


def get_users():
    """Get all current users."""
    return UserRepository().all()


def get_user(user_id):
    """Get the user with a given id.

    :param user_id: the integer id of the user
    """
    return UserRepository().get(user_id=user_id)


def get_user_team(user):
    """Get the team associated with a given user.

    :param user: the user
    """
    user_repository = UserRepository()
    team_repository = TeamRepository()

    return team_repository.get(team_id=user_repository.get_team(user))


def get_teams():
    """Get all current teams."""
    return TeamRepository().all()


def get_team(team_id):
    """Get the team with a given id.

    :param team_id: the integer id of the team
    """
    return TeamRepository().get(team_id=team_id)
