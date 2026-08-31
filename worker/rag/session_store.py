import json
from typing import Protocol, Any

class SessionStore(Protocol):
    async def get(self, session_id: str) -> dict[str, Any]:
        ...

    async def set(self, session_id: str, data: dict[str, Any]) -> None:
        ...


class InMemorySessionStore(SessionStore):
    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def get(self, session_id: str) -> dict[str, Any]:
        return self._store.get(session_id, {}).copy()

    async def set(self, session_id: str, data: dict[str, Any]) -> None:
        self._store[session_id] = data.copy()


class RedisSessionStore(SessionStore):
    def __init__(self, redis_client):
        self._redis = redis_client

    async def get(self, session_id: str) -> dict[str, Any]:
        data = await self._redis.get(session_id)
        if data:
            return json.loads(data)
        return {}

    async def set(self, session_id: str, data: dict[str, Any]) -> None:
        await self._redis.set(session_id, json.dumps(data), ex=3600)  # 1 hour expiry
