from . import db
from .entity import Entity


class Server(Entity):
    def is_idle(self):
        return self._fetch('status') == 'IDLE'

    def is_busy(self):
        return self._fetch('status') == 'BUSY'

    def is_offline(self):
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT asked_server.status='OFFLINE' OR"
                "       TIMESTAMPDIFF(SECOND, asked_server.heartbeat, NOW()) >"
                "       required_setting.value"
                " FROM servers AS asked_server, settings AS required_setting"
                " WHERE asked_server.id=%s AND"
                "       required_setting.name='server_timeout'", (self.id()))
            r = cursor.fetchone()
            return bool(r[0]) if r is not None else False

    def set_idle(self):
        return self._update('status', 'IDLE')

    def set_busy(self):
        return self._update('status', 'BUSY')

    def set_offline(self):
        return self._update('status', 'OFFLINE')

    def update_heartbeat(self):
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE servers SET heartbeat=NOW() WHERE id=%s", (self.id()))

    @staticmethod
    def _jsonify(row):
        keys = [
            "id",
            "status"
        ]
        return dict(zip(keys, row))

    @staticmethod
    def create(server_id):
        with db.cursor() as cursor:
            cursor.execute("REPLACE INTO servers"
                           " (id, status, heartbeat)"
                           " VALUES (%s, %s, NOW()) RETURNING id",
                           (server_id, 'IDLE'))
            return Server(*cursor.fetchone())

    @staticmethod
    def list(jsonify=False):
        if jsonify:
            with db.cursor() as cursor:
                cursor.execute("SELECT id, status FROM projects ORDER BY id")
                return [Server._jsonify(row) for row in cursor]

        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM servers ORDER BY id DESC")
            return [Server(*row) for row in cursor]

    def _fetch(self, field):
        with db.cursor() as cursor:
            cursor.execute(f"SELECT {field} FROM servers WHERE id=%s",
                           (self.id()))
            r = cursor.fetchone()
            return r[0] if r is not None else None

    def _update(self, field, value):
        with db.cursor() as cursor:
            cursor.execute(f"UPDATE servers SET {field}=%s WHERE id=%s",
                           (value, self.id()))
