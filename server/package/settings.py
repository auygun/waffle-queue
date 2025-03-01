from . import db


def waffle_root():
    return _fetch('waffle_root')


def storage_dir():
    return _fetch('storage_dir')


def _fetch(name):
    with db.cursor() as cursor:
        cursor.execute("SELECT value FROM settings WHERE name=%s", (name))
        return cursor.fetchone()[0]
