from typing import Union

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient

from freedium_library.utils.json import json

from ..models import CacheResponse
from .base import AbstractCacheBackend


class MongoDBCacheBackend(AbstractCacheBackend):
    def __init__(
        self,
        connection_string: str,
        database: str = "freedium_cache",
        collection: str = "cache",
    ):
        self.connection_string = connection_string
        self.database_name = database
        self.collection_name = collection
        self.client = None
        self.db = None
        self.collection = None
        self.connect()

    def connect(self):
        self.client = pymongo.MongoClient(self.connection_string)
        self.db = self.client[self.database_name]
        self.collection = self.db[self.collection_name]

    def ensure_connection(self):
        if self.client is None:
            self.connect()

    def init_db(self):
        self.ensure_connection()
        self.collection.create_index("key", unique=True)

    def all(self):
        self.ensure_connection()
        return list(self.collection.find())

    def all_length(self) -> int:
        self.ensure_connection()
        return self.collection.count_documents({})

    def random(self, size: int) -> list[CacheResponse]:
        self.ensure_connection()
        pipeline = [{"$sample": {"size": size}}]
        results = self.collection.aggregate(pipeline)
        return [CacheResponse(doc["key"], doc["value"]) for doc in results]

    def pull(self, key: str) -> Union[CacheResponse, None]:
        self.ensure_connection()
        doc = self.collection.find_one({"key": key})
        if doc:
            logger.debug("Value found in DB, returning it")
            return CacheResponse(key, doc["value"])
        logger.debug(f"No value found for key: {key}")
        return None

    def push(self, key: str, value: Union[str, dict]) -> None:
        if isinstance(value, dict):
            value = json.dumps(value)
        elif not isinstance(value, str):
            raise ValueError(
                f"value argument should be a string or dict, not {type(value).__name__}"
            )

        self.ensure_connection()
        self.collection.update_one(
            {"key": key}, {"$set": {"key": key, "value": value}}, upsert=True
        )

    def delete(self, key: str) -> None:
        self.ensure_connection()
        result = self.collection.delete_one({"key": key})
        if result.deleted_count > 0:
            logger.debug(f"Deleted key: {key}")
        else:
            logger.warning(f"Attempted to delete non-existing key: {key}")

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.collection = None


class AsyncMongoDBCacheBackend(AbstractCacheBackend):
    def __init__(
        self,
        connection_string: str,
        database: str = "cache_db",
        collection: str = "cache",
    ):
        self.connection_string = connection_string
        self.database_name = database
        self.collection_name = collection
        self.client = None
        self.db = None
        self.collection = None
        self.connect()

    def connect(self):
        self.client = AsyncIOMotorClient(self.connection_string)
        self.db = self.client[self.database_name]
        self.collection = self.db[self.collection_name]

    async def aensure_connection(self):
        if self.client is None:
            self.connect()

    async def ainit_db(self):
        await self.aensure_connection()
        await self.collection.create_index("key", unique=True)

    async def aall(self):
        await self.aensure_connection()
        return await self.collection.find().to_list(None)

    async def aall_length(self) -> int:
        await self.aensure_connection()
        return await self.collection.count_documents({})

    async def arandom(self, size: int) -> list[CacheResponse]:
        await self.aensure_connection()
        pipeline = [{"$sample": {"size": size}}]
        results = await self.collection.aggregate(pipeline).to_list(None)
        return [CacheResponse(doc["key"], doc["value"]) for doc in results]

    async def aclose(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.collection = None
