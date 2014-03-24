Leaderboard
===========

A simple Heroku-based, Postgres-backed leaderboard REST API for keeping track of "competitors" in a volunteer-service competition.

Misc. Notes
-----------

 -  Unit tests are too tightly coupled to the actual underlying data model and could use refactoring in that respect.
 -  A better solution for implementing data-type repositories would be to use Postgres' stored procedures for DB access,
    which is both more efficient and has the nice side effect of separation of concerns by keeping SQL out of Python source.
