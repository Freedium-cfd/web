import unittest
from loguru import logger
from database_lib.cache_db import SQLiteCacheBackend
import os
import random
import string

class TestSQLiteCacheBackend(unittest.TestCase):
    test_db = 'test_cache.db'

    @classmethod
    def setUpClass(cls):
        cls.cache_backend = SQLiteCacheBackend(cls.test_db)
        cls.cache_backend.init_db()
        # cls.cache_backend.migrate_add_index_to_key()
        cls.cache_backend.enable_zstd()
        logger.debug(cls.cache_backend.show_schema_info())

    @classmethod
    def tearDownClass(cls):
        cls.cache_backend.close()
        os.remove(cls.test_db)

    def test_push_and_pull(self):
        def generate_random_key(length=10):
            return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

        def generate_random_value():
            return {generate_random_key(5): random.randint(1, 1000) for _ in range(3)}

        def generate_data():
            for _ in range(300):
                yield generate_random_key(), generate_random_value()

        for key, value in generate_data():
            self.cache_backend.push(key, value)
            result = self.cache_backend.pull(key)
            self.assertEqual(result.json(), value, f"The pulled value for key '{key}' should match the pushed value.")
    def test_delete(self):
        key, value = 'delete_key', 'delete_value'
        self.cache_backend.push(key, value)
        self.cache_backend.delete(key)
        result = self.cache_backend.pull(key)
        self.assertIsNone(result, "The result should be None after deletion.")

    def test_all_length(self):
        initial_length = self.cache_backend.all_length()
        self.cache_backend.push('length_keyadsa', {"fsd": 123})
        new_length = self.cache_backend.all_length()
        self.assertEqual(new_length, initial_length + 1, "The length should increase by 1 after adding a new item.")

    def test_random(self):
        # Ensure there is at least one item
        self.cache_backend.push('random_key', 'random_value')
        result = self.cache_backend.random(1)
        self.assertTrue(len(result) > 0, "Should return at least one item.")

    @unittest.skip("Disabling this test temporarily")
    def test_migration_add_index_to_key(self):
        # Forcefully remove the index if it exists to simulate a scenario where the migration is needed.
        self.cache_backend.cursor.execute("DROP INDEX IF EXISTS idx_key")
        self.cache_backend.connection.commit()

        # Call the migration method to add the index.
        self.cache_backend.migrate_add_index_to_key()

        # Verify the index has been created.
        index_exists = self.cache_backend.cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_key'").fetchone()
        self.assertIsNotNone(index_exists, "The index 'idx_key' should exist after migration.")

        # Call the migration method again to simulate the scenario where the index already exists.
        self.cache_backend.migrate_add_index_to_key()

        # Verify that the index still exists and there are no errors.
        index_exists = self.cache_backend.cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_key'").fetchone()
        self.assertIsNotNone(index_exists, "The index 'idx_key' should still exist after calling migration again.")

        # self.cache_backend.cursor.execute("DROP INDEX IF EXISTS idx_key")
        # self.cache_backend.connection.commit()

if __name__ == '__main__':
    unittest.main()