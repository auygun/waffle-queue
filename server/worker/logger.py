from pymysql.err import InterfaceError
import db


class Logger:
    def __init__(self, build_id_cb):
        self._build_id_cb = build_id_cb

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
            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO logs (build_id, severity, message)"
                    " VALUES (%s, %s, %s)",
                    (self._build_id_cb(), severity, message))
            if commit:
                db.commit()
        except InterfaceError:
            # Can happen when task gets canceled due to disconnection
            pass
