import sqlite3
import asyncio
import pickle
from cache_db import SQLiteCacheBackend

db_path = "../medium_cache.sqlite"

async def main():
    conn = sqlite3.connect(db_path)
    db_cache = SQLiteCacheBackend("medium_db_cache.sqlite")
    db_cache.init_db()

    c = conn.cursor()

    c.execute("SELECT * FROM responses")

    results = c.fetchall()

    for result in results:
        value_raw = pickle.loads(result[1])
        db_cache.push(result[0], await value_raw.text())

    # Close the connections
    c.close()
    conn.close()

    db_cache.enable_zstd()

    db_cache.close()

asyncio.run(main())