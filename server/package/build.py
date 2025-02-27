from . import db
from .entity import Entity


class Build(Entity):
    def request(self):
        return self._fetch('request')

    def worker_id(self):
        return self._fetch('worker_id')

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

    def is_open(self):
        return self._fetch('state') in {'BUILDING', 'REQUESTED'}

    def set_succeeded(self):
        return self._update('state', 'SUCCEEDED')

    def set_failed(self):
        return self._update('state', 'FAILED')

    def abort(self):
        with db.cursor() as cursor:
            cursor.execute("UPDATE builds SET state = CASE "
                           "WHEN (state='REQUESTED' OR state='BUILDING') "
                           "THEN 'ABORTED' ELSE state "
                           "END WHERE id=%s", (self.id()))

    @staticmethod
    def _jsonify(row):
        keys = [
            "id",
            "request_id",
            "worker_id",
            "build_config",
            "remote_url",
            "source_branch",
            "build_script",
            "state"
        ]
        return dict(zip(keys, row))

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
    def list(request, jsonify=False):
        if jsonify:
            with db.cursor() as cursor:
                cursor.execute("SELECT id, request, worker_id, build_config,"
                               "       remote_url, source_branch, build_script,"
                               "       state"
                               " FROM builds WHERE request=%s"
                               " ORDER BY id DESC", (request))
                return [Build._jsonify(row) for row in cursor]

        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM builds WHERE request=%s"
                           " ORDER BY id DESC", (request))
            return [Build(*row) for row in cursor]

    @staticmethod
    def pop_next_build_request(worker_id):
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
                cursor.execute("UPDATE builds SET"
                               " state='BUILDING', worker_id=%s"
                               " WHERE id=%s", (worker_id, build.id()))
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
