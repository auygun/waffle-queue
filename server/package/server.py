from . import db
from .entity import Entity


class Server(Entity):
    def status(self):
        return self._fetch('status')

    def set_status(self, value):
        return self._update('status', value)

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

    def update_heartbeat(self):
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE servers SET heartbeat=NOW() WHERE id=%s", (self.id()))

    def jsonify(self):
        return {
            "id": self.id(),
            "status": self.status()
        }

    @staticmethod
    def create(server_id):
        with db.cursor() as cursor:
            cursor.execute("REPLACE INTO servers"
                           " (id, status, heartbeat)"
                           " VALUES (%s, %s, NOW()) RETURNING id",
                           (server_id, 'IDLE'))
            return Server(*cursor.fetchone())

    @staticmethod
    def count():
        with db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM servers")
            return cursor.fetchone()[0]

    @staticmethod
    def list(jsonify=False):
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM servers ORDER BY id DESC")
            if jsonify:
                return [Server(*row).jsonify() for row in cursor]
            return [Server(*row) for row in cursor]

    @staticmethod
    def clear():
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM servers")

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
