from collections import namedtuple
from . import db
from .entity import Entity


BuildConfig = namedtuple(
    'BuildConfig', ['name', 'build_script', 'work_dir', 'output_file'])


class Project(Entity):
    def name(self):
        return self._fetch('name')

    def remote_url(self):
        return self._fetch('remote_url')

    def build_configs(self):
        with db.cursor() as cursor:
            cursor.execute("SELECT name, build_script, work_dir, output_file"
                           " FROM build_configs WHERE project=%s",
                           (self.id()))
            return [BuildConfig(*row) for row in cursor]

    @staticmethod
    def _jsonify(row):
        keys = [
            "id",
            "name",
            "remote_url"
        ]
        return dict(zip(keys, row))

    @staticmethod
    def create(name, remote_url):
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO projects"
                           " (name, remote_url)"
                           " VALUES (%s, %s) RETURNING id",
                           (name, remote_url))
            return Project(*cursor.fetchone())

    @staticmethod
    def list(jsonify=False):
        if jsonify:
            with db.cursor() as cursor:
                cursor.execute("SELECT id, name, remote_url"
                               " FROM projects ORDER BY id")
                return [Project._jsonify(row) for row in cursor]

        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM projects ORDER BY id")
            return [Project(*row) for row in cursor]

    def _fetch(self, field):
        with db.cursor() as cursor:
            cursor.execute(f"SELECT {field} FROM projects WHERE id=%s",
                           (self.id()))
            r = cursor.fetchone()
            return r[0] if r is not None else None
