from pymysql.err import InterfaceError
import db


# pylint:disable = too-few-public-methods
class Logger:
    def __init__(self, build_id_cb):
        self._build_id_cb = build_id_cb

    def log(self, severity, message, commit=True):
        try:
            with db.cursor() as cursor:
                cursor.execute("INSERT INTO logs "
                            "(build_id, severity, message) "
                            "VALUES (%s, %s, %s)",
                            (self._build_id_cb(), severity, message))
            if commit:
                db.commit()
        except InterfaceError:
            # Can happen when task gets canceled due to disconnection
            pass
