from . import db
from .entity import Entity


class Build(Entity):
    def request(self):
        return self._fetch('request')

    def build_config(self):
        return self._fetch('build_config')

    def remote_url(self):
        return self._fetch('remote_url')

    def source_branch(self):
        return self._fetch('source_branch')

    def build_script(self):
        return self._fetch('build_script')

    def work_dir(self):
        return self._fetch('work_dir')

    def state(self):
        return self._fetch('state')

    def is_open(self):
        state = self._fetch('state')
        return state in {'BUILDING', 'REQUESTED'}

    def is_building(self):
        return self._fetch('state') == 'BUILDING'

    def is_succeeded(self):
        return self._fetch('state') == 'SUCCEEDED'

    def set_state(self, value):
        return self._update('state', value)

    def abort(self):
        with db.cursor() as cursor:
            cursor.execute("UPDATE builds SET state = CASE "
                           "WHEN (state='REQUESTED' OR state='BUILDING') "
                           "THEN 'ABORTED' ELSE state "
                           "END WHERE id=%s", (self.id()))

    def jsonify(self):
        return {
            "id": self.id(),
            "request": self.request(),
            "build_config": self.build_config(),
            "remote_url": self.remote_url(),
            "source_branch": self.source_branch(),
            "build_script": self.build_script(),
            "state": self.state()
        }

    # pylint:disable = too-many-arguments
    @staticmethod
    def create(request, build_config, remote_url, source_branch, build_script,
               work_dir, state='REQUESTED'):
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO builds"
                           " (request, build_config, remote_url, source_branch,"
                           "  build_script, work_dir, state)"
                           " VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                           (request, build_config, remote_url, source_branch,
                            build_script, work_dir, state))
            return Build(*cursor.fetchone())

    @staticmethod
    def count(request):
        with db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM builds"
                           " WHERE request=%s", (request))
            return cursor.fetchone()[0]

    @staticmethod
    def list(request, jsonify=False):
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM builds WHERE request=%s"
                           " ORDER BY id DESC", (request))
            if jsonify:
                return [Build(*row).jsonify() for row in cursor]
            return [Build(*row) for row in cursor]

    @staticmethod
    def clear():
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM builds")

    @staticmethod
    def pop_next_build_request():
        # Fetch the next available build request from the queue and mark it as
        # building.
        build = None
        db.commit()  # Start new transaction
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM builds"
                           " WHERE state='REQUESTED'"
                           " ORDER BY id"
                           " FOR UPDATE SKIP LOCKED")
            build_id = cursor.fetchone()
            if build_id is not None:
                build = Build(*build_id)
                build.set_state('BUILDING')
        db.commit()  # Release locks
        return build

    def _fetch(self, field):
        with db.cursor() as cursor:
            cursor.execute(f"SELECT {field} FROM builds WHERE id=%s",
                           (self.id()))
            r = cursor.fetchone()
            return r[0] if r is not None else None

    def _update(self, field, value):
        with db.cursor() as cursor:
            cursor.execute(f"UPDATE builds SET {field}=%s WHERE id=%s",
                           (value, self.id()))
