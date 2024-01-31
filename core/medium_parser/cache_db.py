from typing import Union
import sqlite3
import json
from warnings import warn
try:
    import sqlite_zstd
except ImportError:
    warn("Can't use zstd compression. Please install 'sqlite_zstd' package")
    sqlite_zstd = None

class CacheResponse:
    __slots__ = ('data')
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
        self.connection.execute("PRAGMA foreign_keys = ON")  # Need for working with foreign keys in db
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA auto_vacuum=full")
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
            return self.cursor.execute("SELECT * FROM cache ORDER BY RANDOM() LIMIT :0", {'0': size}).fetchall()

    def enable_zstd(self):
        if sqlite_zstd is None:
            raise ValueError("Can't use zstd compression. Please install 'sqlite_zstd' package")
        
        with self.connection:
            self.cursor.execute("SELECT zstd_enable_transparent('{\"table\": \"cache\", \"column\": \"value\", \"compression_level\": 9, \"dict_chooser\": \"''a''\"}')")
            try:
                self.connection.execute("PRAGMA auto_vacuum=full")
            except Exception as error:
                print(error)
            self.cursor.execute("SELECT zstd_incremental_maintenance(null, 1);")
            self.cursor.execute("vacuum;")

    def init_db(self):
        with self.connection:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT)")

    def pull(self, key: str) -> Union[dict, str]:
        with self.connection:
            cache = self.cursor.execute("SELECT value FROM cache WHERE key = :0", {'0': key}).fetchone()
            if cache:
                return CacheResponse(cache[0])

    def push(self, key: str, value: str) -> None:
        if isinstance(value, dict):
            value = json.dumps(value)
        elif not isinstance(value, str):
            raise ValueError(f"value argument should be only string type not {type(value).__name__}")
        with self.connection:
            self.cursor.execute("INSERT OR REPLACE INTO cache VALUES (:0, :1)", {'0': key, '1': value})

    def delete(self, key: str) -> None:
        with self.connection:
            self.cursor.execute("DELETE FROM cache WHERE key = :0", {'0': key})

    def close(self):
        self.__del__()

    def __del__(self) -> None:
        self.connection.close()
