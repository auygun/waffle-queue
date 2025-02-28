from contextlib import contextmanager

from pymysql.err import OperationalError, InterfaceError
from . import db


class Logger:
    def __init__(self, server_id):
        self._server_id = server_id

    @staticmethod
    def clear():
        try:
            with db.cursor() as cursor:
                cursor.execute("DELETE FROM logs WHERE timestamp <"
                               " (SELECT DATE_SUB(NOW(), INTERVAL value DAY)"
                               "  FROM settings"
                               "  WHERE name='log_retention_days')")
        except (OperationalError, InterfaceError):
            # Can happen when task gets canceled due to disconnection
            return

    @staticmethod
    def list(server_id, max_severity='TRACE'):
        with db.cursor() as cursor:
            cursor.execute("SELECT timestamp, severity, message"
                           " FROM logs WHERE severity<="
                           " (SELECT rank FROM log_level"
                           "  WHERE severity=%s and server_id=%s)"
                           " ORDER BY id",
                           (max_severity, server_id))
            return "\n".join(
                [str(row[0]) + " " + str(row[1]) + "\t" + str(row[2])
                 for row in cursor])

    @staticmethod
    def is_log_on(severity):
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT asked_level.rank <= required_level.rank"
                " FROM log_level AS asked_level, log_level AS required_level"
                " WHERE asked_level.severity=%s AND required_level.severity="
                "  (SELECT value FROM settings WHERE name='log_level')",
                (severity))
            r = cursor.fetchone()
            return bool(r[0]) if r is not None else False

    @contextmanager
    def bulk_logger(self, severity):
        def log(message):
            if message:
                self._log(severity, message)

        def noop(_message):
            pass

        if not Logger.is_log_on(severity):
            yield noop
            return
        try:
            yield log
        except (OperationalError, InterfaceError):
            # Can happen when task gets canceled due to disconnection
            return
        # pylint:disable = bare-except
        try:
            db.commit()
        except:
            pass

    def log(self, severity, message, commit=True):
        try:
            if not message or not Logger.is_log_on(severity):
                return
            self._log(severity, message)
            if commit:
                db.commit()
        except (OperationalError, InterfaceError):
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
