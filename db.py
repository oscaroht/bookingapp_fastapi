from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

from config import settings  # env variables

load_dotenv()

POOL = SimpleConnectionPool(
    minconn=1,
    maxconn=5,  # if your code opens more connections than maxconn and exception will be thrown
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    dbname=settings.DB_NAME,
)


class DatabaseConnection:
    """
    Database context manager for the connection pool.

    A connection can be borrowed from the pool using the with command (context manager).

    Example:
     with Database() as db:
        db.cursor.execute("SELECT ..")
        db.cursor.commit()

    Note:
        If you forget to COMMIT the transaction self.cursor.close() is called in the
        __exit__ function. This will ROLLBACK any open transaction.

        If the number of connections requested exceeds POOL.maxconn psycopg2 will throw an exception. This exception is
        not handled.
    """
    def __init__(self):
        pass

    def __enter__(self):
        self.connection = POOL.getconn()
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        return self

    def __exit__(self, exception_type, exc_val, traceback):
        connection = self.cursor.connection
        self.cursor.close()
        POOL.putconn(connection)
