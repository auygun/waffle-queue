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

    def is_requested(self):
        return self._fetch('state') == 'REQUESTED'

    def is_building(self):
        return self._fetch('state') == 'BUILDING'

    def is_succeeded(self):
        return self._fetch('state') == 'SUCCEEDED'

    def is_failed(self):
        return self._fetch('state') == 'FAILED'

    def is_aborted(self):
        return self._fetch('state') == 'ABORTED'

    def set_building(self):
        return self._update('state', 'BUILDING')

    def set_succeeded(self):
        return self._update('state', 'SUCCEEDED')

    def set_failed(self):
        return self._update('state', 'FAILED')

    def abort(self):
        with db.cursor() as cursor:
            cursor.execute("UPDATE requests SET state = CASE "
                           "WHEN (state='REQUESTED' OR state='BUILDING') "
                           "THEN 'ABORTED' ELSE state "
                           "END WHERE id=%s", (self.id()))

    @staticmethod
    def _jsonify(row):
        keys = [
            "id",
            "project",
            "integration",
            "source_branch",
            "target_branch",
            "state"
        ]
        return dict(zip(keys, row))

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
        if jsonify:
            with db.cursor() as cursor:
                cursor.execute("SELECT id, project, integration, source_branch,"
                               "       target_branch, state"
                               " FROM requests ORDER BY id DESC"
                               " LIMIT %s OFFSET %s", (limit, offset))
                return [Request._jsonify(row) for row in cursor]

        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM requests ORDER BY id DESC"
                           " LIMIT %s OFFSET %s", (limit, offset))
            return [Request(*row) for row in cursor]

    @staticmethod
    def get_new_requests():
        return Request._get_requests('REQUESTED')

    @staticmethod
    def get_building_requests():
        return Request._get_requests('BUILDING')

    @staticmethod
    def _get_requests(state):
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM requests WHERE state=%s"
                           " ORDER BY id", (state))
            return [Request(*row) for row in cursor]

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
