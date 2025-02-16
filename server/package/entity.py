class Entity:
    def __init__(self, id_):
        self._id = id_

    def __eq__(self, other):
        return isinstance(other, Entity) and self._id == other._id

    def __hash__(self):
        return hash(self._id)

    def id(self):
        return self._id

    def is_valid(self):
        return self._fetch("id") is not None

    def _fetch(self, _field):
        pass
