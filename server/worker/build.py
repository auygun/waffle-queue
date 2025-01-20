import db
from entity import Entity


class Build(Entity):
    def branch(self):
        return self._fetch('branch')

    def state(self):
        return self._fetch('state')

    def set_state(self, value):
        return self._update('state', value)

    @staticmethod
    def pop_next_build_request():
        # Fetch the next available build request from the queue and mark it as
        # building.
        build = None
        db.commit()  # Start new transaction
        with db.cursor() as cursor:
            build_ids = cursor.execute("SELECT id FROM builds "
                                       "WHERE state='REQUESTED' "
                                       "ORDER BY id "
                                       "FOR UPDATE SKIP LOCKED")
            build_ids = cursor.fetchone()
            if build_ids is not None:
                build = Build(build_ids[0])
                build.set_state('BUILDING')
        db.commit()  # Release locks
        return build

    def _fetch(self, field):
        with db.cursor() as cursor:
            cursor.execute(f"SELECT {field} FROM builds "
                           "WHERE id=%s",
                           (self.id()))
            r = cursor.fetchone()
            return r[0] if r is not None else None

    def _update(self, field, value):
        with db.cursor() as cursor:
            cursor.execute("UPDATE builds "
                           f"SET {field}=%s "
                           "WHERE id=%s",
                           (value, self.id()))
