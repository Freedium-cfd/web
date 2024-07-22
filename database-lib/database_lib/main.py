import orjson as json
import time
import sqlite3
import threading
from itertools import islice
from typing import Union, Optional
from abc import ABC, abstractmethod

import psycopg2
import sqlite_zstd
import uuid
from loguru import logger
from psycopg2.extras import execute_batch


class CacheData:
    __slots__ = ("data",)

    def __init__(self, data: str):
        self.data = data

    def json(self):
        return json.loads(self.data)

    def __repr__(self):
        return self.data

    def __str__(self):
        return self.data


class CacheResponse:
    __slots__ = ("key", "data")

    def __init__(self, key: str, data: Union[CacheData, str]):
        self.key: str = key
        self.data: CacheData = CacheData(data) if isinstance(data, str) else data

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
    __slots__ = ("connection", "cursor", "database", "lock")

    def __init__(self, database: str, zstd_enabled: bool = False):
        self.database = database
        self.connection = sqlite3.connect(database, timeout=10.0)
        self.connection.enable_load_extension(True)  # Enable loading of extensions
        self.connection.execute("PRAGMA foreign_keys = ON;")  # Need for working with foreign keys in db
        self.connection.execute("PRAGMA journal_mode=WAL;")  # Need to properly work with ZSTD compression
        self.connection.execute("PRAGMA auto_vacuum=full;")  # Same as above thing
        self.cursor = self.connection.cursor()
        self.lock = threading.Lock()

        if zstd_enabled:
            sqlite_zstd.load(self.connection)
            # self.enable_zstd()

    def all(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM cache").fetchall()

    def all_length(self) -> int:
        with self.connection:
            return self.cursor.execute("SELECT COUNT(*) FROM cache").fetchone()[0]

    def random(self, size: int) -> list[CacheResponse]:
        with self.connection:
            self.cursor.execute("SELECT key, value FROM cache ORDER BY RANDOM() LIMIT ?", (size,))
            return [CacheResponse(key, value) for key, value in self.cursor]

    def enable_zstd(self):
        if not self.zstd_enabled:
            raise ValueError("Can't use zstd compression. Please install 'sqlite_zstd' package")

        with self.connection:
            try:
                self.cursor.execute('SELECT zstd_enable_transparent(\'{"table": "cache", "column": "value", "compression_level": 9, "dict_chooser": "\'\'a\'\'"}\')')
            except Exception as error:
                logger.error(f"Error enabling ZSTD compression: {error}")
                logger.exception(error)

            self.connection.execute("PRAGMA auto_vacuum=full")

    def init_db(self):
        with self.connection:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT)")
            # self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_key ON cache (key)")

    def pull(self, key: str) -> Union[CacheResponse, None]:
        with self.connection:
            cache = self.cursor.execute("SELECT value FROM cache WHERE key = :0", {"0": key}).fetchone()
            if cache:
                logger.debug("Value found in DB, returning it")
                return CacheResponse(key, cache[0])
            else:
                logger.debug(f"No value found for key: {key}")
                return None

    def push(self, key: str, value: Union[str, dict]) -> None:
        if isinstance(value, dict):
            try:
                value = json.dumps(value)
            except TypeError as e:
                raise ValueError(f"Unable to serialize value to JSON: {e}")
        elif not isinstance(value, str):
            raise ValueError(f"value argument should be a string or dict, not {type(value).__name__}")

        with self.lock:
            with self.connection:
                self.cursor.execute("INSERT OR REPLACE INTO cache VALUES (:0, :1)", {"0": key, "1": value})

    def delete(self, key: str) -> None:
        with self.connection:
            result = self.cursor.execute("SELECT 1 FROM cache WHERE key = :0", {"0": key}).fetchone()
            if result:
                self.cursor.execute("DELETE FROM cache WHERE key = :0", {"0": key})
                logger.debug(f"Deleted key: {key}")
            else:
                logger.debug(f"Attempted to delete non-existing key: {key}")

    def _generate_test_data(self, num_rows: int, batch_size: int = 10000):
        logger.info("Generating test data")
        with self.connection:
            # Fetch a random key-value pair just once
            self.cursor.execute("SELECT key, value FROM cache ORDER BY RANDOM() LIMIT 1")
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
                print(f"Inserted {min(offset + batch_size, num_rows)} / {num_rows} rows")

    def maintenance(self, time: Optional[int] = None, blocking_time: float = 0.5):
        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()
        connection.enable_load_extension(True)  # Enable loading of extensions
        connection.execute("PRAGMA foreign_keys = ON;")  # Need for working with foreign keys in db
        connection.execute("PRAGMA journal_mode=WAL;")  # Need to properly work with ZSTD compression
        connection.execute("PRAGMA auto_vacuum=full;")  # Same as above thing

        if sqlite_zstd is not None:
            sqlite_zstd.load(connection)

        with connection:
            if time is not None:
                cursor.execute("SELECT zstd_incremental_maintenance(?, ?);", (time, blocking_time))
            else:
                cursor.execute("SELECT zstd_incremental_maintenance(null, ?);", (blocking_time,))
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")

        cursor.close()
        connection.close()

    def maintenance_thread(self):
        maintenance_thread = threading.Thread(target=self.maintenance, daemon=True)
        maintenance_thread.start()

    def show_schema_info(self):
        with self.connection:
            return self.connection.execute("SELECT sql FROM sqlite_master").fetchall()

    def close(self):
        self.__del__()

    def __del__(self) -> None:
        self.connection.close()


class PostgreSQLCacheBackend(AbstractCacheBackend):
    def __init__(self, connection_string: str):
        self.connection = psycopg2.connect(connection_string)
        self.cursor = self.connection.cursor()

    def init_db(self):
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
        with self.connection:
            self.cursor.execute("SELECT * FROM cache")
            return self.cursor.fetchall()

    def all_length(self) -> int:
        with self.connection:
            self.cursor.execute("SELECT COUNT(*) FROM cache")
            return self.cursor.fetchone()[0]

    def random(self, size: int) -> list[CacheResponse]:
        with self.connection:
            self.cursor.execute("SELECT key, value FROM cache ORDER BY RANDOM() LIMIT %s", (size,))
            return [CacheResponse(key, value) for key, value in self.cursor]

    def pull(self, key: str) -> Union[CacheResponse, None]:
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
                value = json.dumps(value)
            except TypeError as e:
                raise ValueError(f"Unable to serialize value to JSON: {e}")
        elif not isinstance(value, str):
            raise ValueError(f"value argument should be a string or dict, not {type(value).__name__}")

        with self.connection:
            self.cursor.execute("INSERT INTO cache (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", (key, value))

    def delete(self, key: str) -> None:
        with self.connection:
            self.cursor.execute("DELETE FROM cache WHERE key = %s", (key,))
            if self.cursor.rowcount > 0:
                logger.debug(f"Deleted key: {key}")
            else:
                logger.debug(f"Attempted to delete non-existing key: {key}")

    def close(self):
        self.cursor.close()
        self.connection.close()


def migrate_to_postgres(sqlite_db_path: str, pg_conn_string: str, chunk_size: int = 1000):
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
            chunk = sqlite_db.cursor.execute("SELECT key, value FROM cache LIMIT ? OFFSET ?", (chunk_size, processed_rows)).fetchall()
            if not chunk:
                logger.debug("No more rows to process")
                break

            logger.debug(f"Processing chunk of {len(chunk)} rows")
            execute_batch(pg_db.cursor, "INSERT INTO cache (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", chunk)
            pg_db.connection.commit()

            processed_rows += len(chunk)

            elapsed_time = time.time() - start_time
            rows_per_second = processed_rows / elapsed_time
            logger.info(f"Processed {processed_rows}/{total_rows} rows. Speed: {rows_per_second:.2f} rows/second")
    except Exception as e:
        logger.error(f"An error occurred during migration: {e}")
        pg_db.connection.rollback()
    finally:
        sqlite_db.close()
        pg_db.close()
        logger.debug("Database connections closed")

    total_time = time.time() - start_time
    logger.success(f"Data migration to PostgreSQL completed")
    logger.info(f"Total time: {total_time:.2f} seconds. Average speed: {total_rows/total_time:.2f} rows/second")


def execute_migrate_to_postgres_in_thread(sqlite_db_path: str, pg_conn_string: str, chunk_size: int = 1000):
    logger.info("Starting migration to PostgreSQL in thread")
    migration_thread = threading.Thread(target=migrate_to_postgres, args=(sqlite_db_path, pg_conn_string, chunk_size), daemon=True)
    migration_thread.start()
    return migration_thread
