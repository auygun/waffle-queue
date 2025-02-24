from contextlib import contextmanager

from pymysql.err import InterfaceError
from . import db


class Logger:
    def __init__(self, server_id):
        self._server_id = server_id

    def list(self, server_id, max_severity=None, jsonify=False):
        if max_severity is None:
            with db.cursor() as cursor:
                cursor.execute("SELECT value FROM settings"
                               " WHERE name='log_level'")
                max_severity = cursor.fetchone()[0]
        with db.cursor() as cursor:
            cursor.execute("SELECT server_id, timestamp, severity, message"
                           " FROM logs WHERE severity<="
                           " (SELECT rank FROM log_level"
                           "  WHERE severity=%s and server_id=%s)"
                           " ORDER BY id",
                           (max_severity, server_id))
            if jsonify:
                keys = ["server_id", "timestamp", "severity", "message"]
                return [dict(zip(keys, row)) for row in cursor]
            else:
                return list(cursor)

    @contextmanager
    def bulk_logger(self, severity):
        def log(message):
            if message:
                self._log(severity, message)

        def noop(_message):
            pass

        if not self.is_log_on(severity):
            yield noop
            return
        try:
            yield log
        except InterfaceError:
            # Can happen when task gets canceled due to disconnection
            return
        # pylint:disable = bare-except
        try:
            db.commit()
        except:
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

    def fatal(self, message, commit=True):
        self.log('FATAL', message, commit)

    def error(self, message, commit=True):
        self.log('ERROR', message, commit)

    def warn(self, message, commit=True):
        self.log('WARN', message, commit)

    def info(self, message, commit=True):
        self.log('INFO', message, commit)

    def debug(self, message, commit=True):
        self.log('DEBUG', message, commit)

    def trace(self, message, commit=True):
        self.log('TRACE', message, commit)

    def _log(self, severity, message):
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO logs (server_id, severity, message)"
                " VALUES (%s, %s, %s)",
                (self._server_id, severity, message))
