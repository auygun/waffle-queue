import pymysql


_conn = None


def open():
    global _conn
    print("db: Opening connection")
    _conn = pymysql.connect(host='127.0.0.1', port=3306,
                            user='mysql', password='mysql',
                            db='builder', autocommit=False,
                            cursorclass=pymysql.cursors.DictCursor)


def close(e=None):
    global _conn
    if _conn is not None:
        print("db: Closing connection")
        _conn.commit()
        _conn.close()
        _conn = None


def ping():
    _conn.ping(reconnect=True)


def cursor():
    return _conn.cursor()


def commit():
    return _conn.commit()


def rollback():
    return _conn.rollback()


def now():
    with _conn.cursor() as cursor:
        cursor.execute("SELECT NOW()")
        return cursor.next()[0]
