import sqlite3
import click
from flask import g
import datetime

import worker

_schema_script = '''
DROP TABLE IF EXISTS builds;
CREATE TABLE builds(id primary key, title, author, read);
'''


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_test_db_command)


def init_db():
    db = get_db()
    with db:
        db.executescript(_schema_script)


def get_db():
    if 'db' not in g:
        print("db: Opening db")
        g.db = sqlite3.connect("file:builder.db?mode=rwc",
                               uri=True, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = lambda cursor, row: dict(
            (cursor.description[idx][0], value) for idx, value in enumerate(row))
        sqlite3.register_converter(
            "timestamp", lambda v: datetime.fromisoformat(v.decode()))
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        print("db: Closing db")
        db.commit()
        db.close()


def query_db(query, args=(), one=False):
    cursor = get_db().execute(query, args)
    rows = cursor.fetchall()
    cursor.close()
    return (rows[0] if rows else None) if one else rows


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    try:
        init_db()
        click.echo('Initialized the database.')
    except sqlite3.OperationalError as e:
        print(e)
    worker.stop()


@click.command('init-test-db')
def init_test_db_command():
    try:
        init_db()
        db = get_db()
        with db:
            BOOKS = [
                {
                    'id': 1,
                    'title': 'On the Road',
                    'author': 'Jack Kerouac',
                    'read': True
                },
                {
                    'id': 2,
                    'title': 'Harry Potter and the Philosopher\'s Stone',
                    'author': 'J. K. Rowling',
                    'read': False
                },
                {
                    'id': 3,
                    'title': 'Green Eggs and Ham',
                    'author': 'Dr. Seuss',
                    'read': True
                }
            ]
            db.executemany(
                "INSERT INTO builds VALUES(:id, :title, :author, :read)", BOOKS)
        click.echo('Initialized the database with test data.')
    except sqlite3.OperationalError as e:
        print(e)
    worker.stop()
