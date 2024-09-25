import codecs
import json as py_json
import sqlite3
import threading
import time
import uuid
from abc import ABC, abstractmethod
from itertools import islice
from typing import Optional, Union

import orjson as json
import psycopg2
from loguru import logger
from psycopg2.extras import execute_batch

try:
    import sqlite_zstd
except ImportError:
    sqlite_zstd = None


class CacheData:
    __slots__ = ("data",)

    def __init__(self, data: str):
        self.data = data

    def json(self):
        try:
            return json.loads(self.data)
        except json.JSONDecodeError:
            logger.warning(
                f"Failed to decode JSON data: {self.data[:100]}... Trying workaround"
            )
            return self.workaround_decode_json()

    def workaround_decode_json(self):
        if self.data.startswith("\\x"):
            s = self.data[2:]
        else:
            s = self.data

        byte_string = codecs.decode(s, "hex")
        json_string = byte_string.decode("utf-8")

        return json.loads(json_string)

    def __repr__(self):
        return self.data

    def __str__(self):
        return self.data

    def has_data(self):
        return self.data is not None and self.data != ""


class CacheResponse:
    __slots__ = ("key", "data")

    def __init__(self, key: str, data: Union[CacheData, str]):
        self.key: str = key
        self.data: CacheData = (
            CacheData(data) if not isinstance(data, CacheData) else data
        )

    def json(self):
        return self.data.json()


class AbstractCacheBackend(ABC):
    @abstractmethod
    def init_db(self):
        pass

    @abstractmethod
    def all(self):
        pass

    @abstractmethod
    def all_length(self) -> int:
        pass

    @abstractmethod
    def random(self, size: int) -> list[CacheResponse]:
        pass

    @abstractmethod
    def pull(self, key: str) -> Union[CacheResponse, None]:
        pass

    @abstractmethod
    def push(self, key: str, value: Union[str, dict]) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def close(self):
        pass


class SQLiteCacheBackend(AbstractCacheBackend):
    __slots__ = ("connection", "cursor", "database", "lock", "zstd_enabled")

    def __init__(self, database: str, zstd_enabled: bool = False):
        self.database = database
        self.connection = None
        self.cursor = None
        self.lock = threading.Lock()
        self.zstd_enabled = zstd_enabled
        self.connect()

    def connect(self):
        self.connection = sqlite3.connect(self.database, timeout=10.0)
        self.connection.enable_load_extension(True)
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self.connection.execute("PRAGMA journal_mode=WAL;")
        self.connection.execute("PRAGMA auto_vacuum=full;")
        self.cursor = self.connection.cursor()

        if self.zstd_enabled:
            if sqlite_zstd is None:
                raise ValueError("sqlite_zstd library not found.")

            sqlite_zstd.load(self.connection)
            self.enable_zstd()

    def ensure_connection(self):
        if self.connection is None or self.cursor is None:
            self.connect()

    def all(self):
        self.ensure_connection()
        with self.connection:
            return self.cursor.execute("SELECT * FROM cache").fetchall()

    def all_length(self) -> int:
        self.ensure_connection()
        with self.connection:
            return self.cursor.execute("SELECT COUNT(*) FROM cache").fetchone()[0]

    def random(self, size: int) -> list[CacheResponse]:
        self.ensure_connection()
        with self.connection:
            self.cursor.execute(
                "SELECT key, value FROM cache ORDER BY RANDOM() LIMIT ?", (size,)
            )
            return [CacheResponse(key, value) for key, value in self.cursor]

    def enable_zstd(self):
        self.ensure_connection()
        with self.connection:
            try:
                self.cursor.execute(
                    'SELECT zstd_enable_transparent(\'{"table": "cache", "column": "value", "compression_level": 9, "dict_chooser": "\'\'a\'\'"}\')'
                )
            except Exception as error:
                logger.error(f"Error enabling ZSTD compression: {error}")
                logger.exception(error)

            self.connection.execute("PRAGMA auto_vacuum=full")

    def init_db(self):
        self.ensure_connection()
        with self.connection:
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT)"
            )
            # self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_key ON cache (key)")

    def pull(self, key: str) -> Union[CacheResponse, None]:
        self.ensure_connection()
        with self.connection:
            cache = self.cursor.execute(
                "SELECT value FROM cache WHERE key = :0", {"0": key}
            ).fetchone()
            if cache:
                logger.debug("Value found in DB, returning it")
                return CacheResponse(key, cache[0])
            else:
                logger.debug(f"No value found for key: {key}")
                return None

    def push(self, key: str, value: Union[str, dict]) -> None:
        if isinstance(value, dict):
            try:
                value = py_json.dumps(value)
            except TypeError as e:
                raise ValueError(f"Unable to serialize value to JSON: {e}")
        elif not isinstance(value, str):
            raise ValueError(
                f"value argument should be a string or dict, not {type(value).__name__}"
            )

        self.ensure_connection()
        with self.lock:
            with self.connection:
                self.cursor.execute(
                    "INSERT OR REPLACE INTO cache VALUES (:0, :1)",
                    {"0": key, "1": value},
                )

    def delete(self, key: str) -> None:
        self.ensure_connection()
        with self.connection:
            result = self.cursor.execute(
                "SELECT 1 FROM cache WHERE key = :0", {"0": key}
            ).fetchone()
            if result:
                self.cursor.execute("DELETE FROM cache WHERE key = :0", {"0": key})
                logger.debug(f"Deleted key: {key}")
            else:
                logger.debug(f"Attempted to delete non-existing key: {key}")

    def _generate_test_data(self, num_rows: int, batch_size: int = 10000):
        logger.info("Generating test data")
        self.ensure_connection()
        with self.connection:
            # Fetch a random key-value pair just once
            self.cursor.execute(
                "SELECT key, value FROM cache ORDER BY RANDOM() LIMIT 1"
            )
            key, value = self.cursor.fetchone()

            # Use a generator to create batches of test data
            def data_generator():
                for i in range(num_rows):
                    yield (f"{uuid.uuid4()}", value)

            # Process data in batches
            for offset in range(0, num_rows, batch_size):
                batch = list(islice(data_generator(), batch_size))
                self.cursor.executemany("INSERT INTO cache VALUES (?, ?)", batch)
                self.connection.commit()
                print(
                    f"Inserted {min(offset + batch_size, num_rows)} / {num_rows} rows"
                )

    def maintenance(self, time: Optional[int] = None, blocking_time: float = 0.5):
        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()
        connection.enable_load_extension(True)  # Enable loading of extensions
        connection.execute(
            "PRAGMA foreign_keys = ON;"
        )  # Need for working with foreign keys in db
        connection.execute(
            "PRAGMA journal_mode=WAL;"
        )  # Need to properly work with ZSTD compression
        connection.execute("PRAGMA auto_vacuum=full;")  # Same as above thing

        if sqlite_zstd is not None:
            sqlite_zstd.load(connection)

        with connection:
            if time is not None:
                cursor.execute(
                    "SELECT zstd_incremental_maintenance(?, ?);", (time, blocking_time)
                )
            else:
                cursor.execute(
                    "SELECT zstd_incremental_maintenance(null, ?);", (blocking_time,)
                )
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")

        cursor.close()
        connection.close()

    def maintenance_thread(self):
        maintenance_thread = threading.Thread(target=self.maintenance, daemon=True)
        maintenance_thread.start()

    def show_schema_info(self):
        self.ensure_connection()
        with self.connection:
            return self.connection.execute("SELECT sql FROM sqlite_master").fetchall()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    def __del__(self):
        self.close()


class PostgreSQLCacheBackend(AbstractCacheBackend):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        self.connection = psycopg2.connect(self.connection_string)
        self.cursor = self.connection.cursor()

    def ensure_connection(self):
        if self.connection is None or self.connection.closed:
            self.connect()
        elif self.cursor is None or self.cursor.closed:
            self.cursor = self.connection.cursor()

    def init_db(self):
        self.ensure_connection()
        with self.connection:
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """
            )

    def all(self):
        self.ensure_connection()
        with self.connection:
            self.cursor.execute("SELECT * FROM cache")
            return self.cursor.fetchall()

    def all_length(self) -> int:
        self.ensure_connection()
        with self.connection:
            self.cursor.execute("SELECT COUNT(*) FROM cache")
            return self.cursor.fetchone()[0]

    def random(self, size: int) -> list[CacheResponse]:
        self.ensure_connection()
        with self.connection:
            self.cursor.execute(
                "SELECT key, value FROM cache ORDER BY RANDOM() LIMIT %s", (size,)
            )
            return [CacheResponse(key, value) for key, value in self.cursor]

    def pull(self, key: str) -> Union[CacheResponse, None]:
        self.ensure_connection()
        with self.connection:
            self.cursor.execute("SELECT value FROM cache WHERE key = %s", (key,))
            cache = self.cursor.fetchone()
            if cache:
                logger.debug("Value found in DB, returning it")
                return CacheResponse(key, cache[0])
            else:
                logger.debug(f"No value found for key: {key}")
                return None

    def push(self, key: str, value: Union[str, dict]) -> None:
        if isinstance(value, dict):
            try:
                value = py_json.dumps(value)
            except TypeError as e:
                raise ValueError(f"Unable to serialize value to JSON: {e}")
        elif not isinstance(value, str):
            raise ValueError(
                f"value argument should be a string or dict, not {type(value).__name__}"
            )

        self.ensure_connection()
        with self.connection:
            self.cursor.execute(
                "INSERT INTO cache (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                (key, value),
            )

    def delete(self, key: str) -> None:
        self.ensure_connection()
        with self.connection:
            self.cursor.execute("DELETE FROM cache WHERE key = %s", (key,))
            if self.cursor.rowcount > 0:
                logger.debug(f"Deleted key: {key}")
            else:
                logger.debug(f"Attempted to delete non-existing key: {key}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.cursor = None
        self.connection = None


def migrate_to_postgres(
    sqlite_db_path: str, pg_conn_string: str, chunk_size: int = 1000
):
    logger.debug(f"Starting migration from SQLite ({sqlite_db_path}) to PostgreSQL")
    sqlite_db = SQLiteCacheBackend(sqlite_db_path, zstd_enabled=True)
    pg_db = PostgreSQLCacheBackend(pg_conn_string)

    # sqlite_db._generate_test_data(15_000_000_000)
    pg_db.init_db()
    logger.debug("PostgreSQL database initialized")

    total_rows = sqlite_db.all_length()
    logger.info(f"Total rows to migrate: {total_rows}")
    processed_rows = 0
    start_time = time.time()

    try:
        while processed_rows < total_rows:
            chunk = sqlite_db.cursor.execute(
                "SELECT key, value FROM cache LIMIT ? OFFSET ?",
                (chunk_size, processed_rows),
            ).fetchall()
            if not chunk:
                logger.debug("No more rows to process")
                break

            logger.debug(f"Processing chunk of {len(chunk)} rows")
            execute_batch(
                pg_db.cursor,
                "INSERT INTO cache (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                chunk,
            )
            pg_db.connection.commit()

            processed_rows += len(chunk)

            elapsed_time = time.time() - start_time
            rows_per_second = processed_rows / elapsed_time
            logger.info(
                f"Processed {processed_rows}/{total_rows} rows. Speed: {rows_per_second:.2f} rows/second"
            )
    except Exception as e:
        logger.error(f"An error occurred during migration: {e}")
        pg_db.connection.rollback()
    finally:
        sqlite_db.close()
        pg_db.close()
        logger.debug("Database connections closed")

    total_time = time.time() - start_time
    logger.success(f"Data migration to PostgreSQL completed")
    logger.info(
        f"Total time: {total_time:.2f} seconds. Average speed: {total_rows/total_time:.2f} rows/second"
    )


def execute_migrate_to_postgres_in_thread(
    sqlite_db_path: str, pg_conn_string: str, chunk_size: int = 1000
):
    logger.info("Starting migration to PostgreSQL in thread")
    migration_thread = threading.Thread(
        target=migrate_to_postgres,
        args=(sqlite_db_path, pg_conn_string, chunk_size),
        daemon=True,
    )
    migration_thread.start()
    return migration_thread
