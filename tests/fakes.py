class InMemoryRedisPipeline:
    def __init__(self, redis: "InMemoryRedis"):
        self.redis = redis
        self.operations: list[tuple[str, str]] = []

    def incr(self, key: str) -> "InMemoryRedisPipeline":
        self.operations.append(("incr", key))
        return self

    def ttl(self, key: str) -> "InMemoryRedisPipeline":
        self.operations.append(("ttl", key))
        return self

    def execute(self) -> list[int]:
        results = []

        for operation, key in self.operations:
            if operation == "incr":
                results.append(self.redis.incr(key))
            elif operation == "ttl":
                results.append(self.redis.ttl(key))

        return results


class InMemoryRedis:
    def __init__(self):
        self.values: dict[str, str] = {}
        self.expires: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self.values[key] = value

        if ex is not None:
            self.expires[key] = ex

        return True

    def delete(self, *keys: str) -> int:
        deleted = 0

        for key in keys:
            if key in self.values:
                deleted += 1
                del self.values[key]

            self.expires.pop(key, None)

        return deleted

    def incr(self, key: str) -> int:
        value = int(self.values.get(key, "0")) + 1
        self.values[key] = str(value)
        return value

    def ttl(self, key: str) -> int:
        if key not in self.values:
            return -2

        return self.expires.get(key, -1)

    def expire(self, key: str, seconds: int) -> bool:
        if key not in self.values:
            return False

        self.expires[key] = seconds
        return True

    def pipeline(self) -> InMemoryRedisPipeline:
        return InMemoryRedisPipeline(self)
