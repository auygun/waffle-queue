from . import db
from .entity import Entity


class Build(Entity):
    def integration(self):
        return self._fetch('integration') == 1

    def remote_url(self):
        return self._fetch('remote_url')

    def source_branch(self):
        return self._fetch('source_branch')

    def target_branch(self):
        return self._fetch('target_branch')

    def build_script(self):
        return self._fetch('build_script')

    def work_dir(self):
        return self._fetch('work_dir')

    def state(self):
        return self._fetch('state')

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
            "integration": self.integration(),
            "remote_url": self.remote_url(),
            "source_branch": self.source_branch(),
            "target_branch": self.target_branch(),
            "build_script": self.build_script(),
            "state": self.state()
        }

    @staticmethod
    def new(integration, remote_url, source_branch, target_branch, build_script,
            work_dir, state='REQUESTED'):
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO builds"
                           " (integration, remote_url, source_branch,"
                           "  target_branch, build_script, work_dir, state)"
                           " VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                           (integration, remote_url, source_branch,
                            target_branch, build_script, work_dir, state))
        return Build(*cursor.fetchone())

    @staticmethod
    def count():
        with db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM builds")
        return cursor.fetchone()[0]

    @staticmethod
    def list(offset, limit, jsonify=False):
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM builds ORDER BY id DESC"
                           " LIMIT %s OFFSET %s", (limit, offset))
            if jsonify:
                return [Build(*row).jsonify() for row in cursor]
            else:
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
            build_ids = cursor.execute("SELECT id FROM builds"
                                       " WHERE state='REQUESTED'"
                                       " ORDER BY id"
                                       " FOR UPDATE SKIP LOCKED")
            build_ids = cursor.fetchone()
            if build_ids is not None:
                build = Build(*build_ids)
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
