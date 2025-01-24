def not_implemented():
    raise NotImplementedError

ping = not_implemented
cursor = not_implemented
commit = not_implemented
rollback = not_implemented
now = not_implemented

def asset_not_implemented():
    assert ping is not_implemented
    assert cursor is not_implemented
    assert commit is not_implemented
    assert rollback is not_implemented
    assert now is not_implemented
