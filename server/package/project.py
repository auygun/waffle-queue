from collections import namedtuple
from . import db
from .entity import Entity


BuildConfig = namedtuple('BuildConfig', ['name', 'build_script', 'work_dir'])


class Project(Entity):
    def name(self):
        return self._fetch('name')

    def remote_url(self):
        return self._fetch('remote_url')

    def build_configs(self):
        with db.cursor() as cursor:
            cursor.execute("SELECT name, build_script, work_dir"
                           " FROM build_configs WHERE project=%s",
                           (self.id()))
            return [BuildConfig(*row) for row in cursor]

    def jsonify(self):
        return {
            "id": self.id(),
            "name": self.name(),
            "remote_url": self.remote_url(),
        }

    @staticmethod
    def create(name, remote_url):
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO projects"
                           " (name, remote_url)"
                           " VALUES (%s, %s) RETURNING id",
                           (name, remote_url))
            return Project(*cursor.fetchone())

    @staticmethod
    def count():
        with db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM projects")
            return cursor.fetchone()[0]

    @staticmethod
    def list(jsonify=False):
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM projects ORDER BY id DESC")
            if jsonify:
                return [Project(*row).jsonify() for row in cursor]
            return [Project(*row) for row in cursor]

    @staticmethod
    def clear():
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM projects")

    def _fetch(self, field):
        with db.cursor() as cursor:
            cursor.execute(f"SELECT {field} FROM projects WHERE id=%s",
                           (self.id()))
            r = cursor.fetchone()
            return r[0] if r is not None else None

    def _update(self, field, value):
        with db.cursor() as cursor:
            cursor.execute(f"UPDATE projects SET {field}=%s WHERE id=%s",
                           (value, self.id()))
