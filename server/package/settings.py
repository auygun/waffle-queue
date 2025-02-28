from . import db


def log_retention_days():
    return int(_fetch('log_retention_days'))


def _fetch(name):
    with db.cursor() as cursor:
        cursor.execute("SELECT value FROM settings WHERE name=%s", (name))
        return cursor.fetchone()[0]
