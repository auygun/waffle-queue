from .. import db as base_db
from . import db

base_db.asset_not_implemented()

base_db.ping = db.ping
base_db.cursor = db.cursor
base_db.commit = db.commit
base_db.rollback = db.rollback
base_db.now = db.now
