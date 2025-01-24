from contextlib import contextmanager

from pymysql.err import InterfaceError
from . import db


class Logger:
    def __init__(self, build_id_cb):
        self._build_id_cb = build_id_cb

    @contextmanager
    def bulk_logger(self, severity):
        def log(message):
            if message:
                self._log(severity, message)

        if not self.is_log_on(severity):
            return
        try:
            yield log
        except InterfaceError:
            # Can happen when task gets canceled due to disconnection
            return
        try:
            db.commit()
        finally:
            pass

    def is_log_on(self, severity):
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT asked_level.rank <= required_level.rank"
                " FROM log_level AS asked_level, log_level AS required_level"
                " WHERE asked_level.severity=%s AND required_level.severity="
                "  (SELECT value FROM settings WHERE name='log_level')",
                (severity))
            r = cursor.fetchone()
            return bool(r[0]) if r is not None else False

    def log(self, severity, message, commit=True):
        try:
            if not message or not self.is_log_on(severity):
                return
            self._log(severity, message)
            if commit:
                db.commit()
        except InterfaceError:
            # Can happen when task gets canceled due to disconnection
            pass

    def _log(self, severity, message):
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO logs (build_id, severity, message)"
                " VALUES (%s, %s, %s)",
                (self._build_id_cb(), severity, message))
