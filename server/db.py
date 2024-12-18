import sqlite3
import click
from flask import g
from datetime import datetime

sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_test_db_command)


def init_db():
    db = get_db()
    with db:
        db.executescript("""
            DROP TABLE IF EXISTS builds;
            CREATE TABLE builds(id, title, author, read)
            """)


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("file:builder.db?mode=rwc",
                               uri=True, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = make_dicts
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.commit()
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


@click.command('init-test-db')
def init_test_db_command():
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
