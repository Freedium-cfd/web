from typing import Union
import sqlite3
import json
from loguru import logger
from warnings import warn
try:
    import sqlite_zstd
except ImportError:
    logger.debug("Can't use zstd compression. Please install 'sqlite_zstd' package")
    warn("Can't use zstd compression. Please install 'sqlite_zstd' package")
    sqlite_zstd = None

class CacheResponse:
    __slots__ = ('data',)
    def __init__(self, data: str):
        self.data = data

    def json(self):
        return json.loads(self.data)

    def __repr__(self):
        return self.data

    def __str__(self):
        return self.data

class SQLiteCacheBackend:
    __slots__ = ('connection', 'cursor')
    def __init__(self, database: str):
        self.connection = sqlite3.connect(database)
        self.connection.enable_load_extension(True)  # Enable loading of extensions
        self.connection.execute("PRAGMA foreign_keys = ON;")  # Need for working with foreign keys in db
        self.connection.execute("PRAGMA journal_mode=WAL;") # Need to properly work with ZSTD compression
        self.connection.execute("PRAGMA auto_vacuum=full;") # Same as above thing
        self.cursor = self.connection.cursor()

        if sqlite_zstd is not None:
            sqlite_zstd.load(self.connection)

    def all(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM cache").fetchall()

    def all_length(self) -> int:
        with self.connection:
            return self.cursor.execute("SELECT COUNT(*) FROM cache").fetchone()[0]

    def random(self, size: int):
        with self.connection:
            return self.cursor.execute("SELECT * FROM cache ORDER BY RANDOM() LIMIT ?", (size,)).fetchall()
    
    def enable_zstd(self):
        if sqlite_zstd is None:
            raise ValueError("Can't use zstd compression. Please install 'sqlite_zstd' package")
        
        with self.connection:
            try:
                self.cursor.execute("SELECT zstd_enable_transparent('{\"table\": \"cache\", \"column\": \"value\", \"compression_level\": 9, \"dict_chooser\": \"''a''\"}')")
            except Exception as error:
                print(error)
            self.connection.execute("PRAGMA auto_vacuum=full")
            self.cursor.execute("SELECT zstd_incremental_maintenance(null, 1);")
            self.cursor.execute("vacuum;")

    def init_db(self):
        with self.connection:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT)")
            # self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_key ON cache (key)")

    def pull(self, key: str) -> Union[CacheResponse, None]:
        with self.connection:
            cache = self.cursor.execute("SELECT value FROM cache WHERE key = :0", {'0': key}).fetchone()
            if cache:
                logger.debug("Value found in DB, returning it")
                return CacheResponse(cache[0])
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
            self.cursor.execute("INSERT OR REPLACE INTO cache VALUES (:0, :1)", {'0': key, '1': value})
            
    def delete(self, key: str) -> None:
        with self.connection:
            result = self.cursor.execute("SELECT 1 FROM cache WHERE key = :0", {'0': key}).fetchone()
            if result:
                self.cursor.execute("DELETE FROM cache WHERE key = :0", {'0': key})
                logger.debug(f"Deleted key: {key}")
            else:
                logger.debug(f"Attempted to delete non-existing key: {key}")
    
    def maintenance(self):
        with self.connection:
            self.cursor.execute("VACUUM")
            self.cursor.execute("ANALYZE")

    def migrate_add_index_to_key(self):
        with self.connection:
            # Check if the index already exists
            index_exists = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_key'").fetchone()
            if not index_exists:
                # Create the index if it doesn't exist
                self.cursor.execute("CREATE INDEX idx_key ON cache (key)")
                logger.info("Index 'idx_key' on column 'key' created successfully.")
            else:
                logger.info("Index 'idx_key' on column 'key' already exists.")

    def show_schema_info(self):
        with self.connection:
            return self.connection.execute("SELECT sql FROM sqlite_master").fetchall()

    def close(self):
        self.__del__()

    def __del__(self) -> None:
        self.connection.close()
