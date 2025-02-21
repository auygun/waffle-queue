from . import db
from .entity import Entity


class Request(Entity):
    def project(self):
        return self._fetch('project')

    def integration(self):
        return self._fetch('integration')

    def source_branch(self):
        return self._fetch('source_branch')

    def target_branch(self):
        return self._fetch('target_branch')

    def state(self):
        return self._fetch('state')

    def set_state(self, value):
        return self._update('state', value)

    def abort(self):
        with db.cursor() as cursor:
            cursor.execute("UPDATE requests SET state = CASE "
                           "WHEN (state='REQUESTED' OR state='BUILDING') "
                           "THEN 'ABORTED' ELSE state "
                           "END WHERE id=%s", (self.id()))

    def jsonify(self):
        return {
            "id": self.id(),
            "project": self.project(),
            "integration": self.integration(),
            "source_branch": self.source_branch(),
            "target_branch": self.target_branch(),
            "state": self.state()
        }

    @staticmethod
    def create(project, integration, source_branch, target_branch,
               state='REQUESTED'):
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO requests"
                           " (project, integration, source_branch,"
                           "  target_branch, state)"
                           " VALUES ((SELECT id FROM projects WHERE name=%s),"
                           "         %s, %s, %s, %s) RETURNING id",
                           (project, integration, source_branch, target_branch,
                            state))
            return Request(*cursor.fetchone())

    @staticmethod
    def count():
        with db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM requests")
            return cursor.fetchone()[0]

    @staticmethod
    def list(offset, limit, jsonify=False):
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM requests ORDER BY id DESC"
                           " LIMIT %s OFFSET %s", (limit, offset))
            if jsonify:
                return [Request(*row).jsonify() for row in cursor]
            return [Request(*row) for row in cursor]

    @staticmethod
    def get_new_requests():
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM requests WHERE state='REQUESTED'"
                           " ORDER BY id")
            return [Request(*row) for row in cursor]

    @staticmethod
    def clear():
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM requests")

    def _fetch(self, field):
        with db.cursor() as cursor:
            cursor.execute(f"SELECT {field} FROM requests WHERE id=%s",
                           (self.id()))
            r = cursor.fetchone()
            return r[0] if r is not None else None

    def _update(self, field, value):
        with db.cursor() as cursor:
            cursor.execute(f"UPDATE requests SET {field}=%s WHERE id=%s",
                           (value, self.id()))
