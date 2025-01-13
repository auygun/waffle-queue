import lazy_object_proxy
import pymysql
import pymysqlpool


def _create_pool():
    print("db: Create pool")
    # pymysqlpool.logger.setLevel('DEBUG')
    return pymysqlpool.ConnectionPool(host='127.0.0.1', port=3306,
                                      user='mysql', password='mysql',
                                      db='waffle_queue', autocommit=True,
                                      cursorclass=pymysql.cursors.DictCursor)


_pool = lazy_object_proxy.Proxy(_create_pool)


def connection():
    return _pool.get_connection()


def now():
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT NOW()")
        return cursor.next()[0]
