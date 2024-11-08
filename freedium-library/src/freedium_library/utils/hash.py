import hashlib
import secrets


class HashLib:
    @staticmethod
    def sha256(data: bytes) -> str:
        sha256_hash = hashlib.sha256()
        sha256_hash.update(data)
        return sha256_hash.hexdigest()

    @staticmethod
    def random_sha256() -> str:
        return HashLib.sha256(secrets.token_bytes())
