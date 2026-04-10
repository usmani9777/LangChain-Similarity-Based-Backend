# from collections import deque
# from typing import Dict, List, Optional
# import logging
# import redis

# logger = logging.getLogger(__name__)


# class DictSessionStore:
#     def __init__(self, max_items: int = 5):
#         self.max_items = max_items
#         self._store: Dict[str, deque] = {}

#     # -----------------------------
#     # Add dictionary to session
#     # -----------------------------
#     def add(
#         self,
#         session_id: str,
#         data: Dict
#     ) -> None:
#         if not session_id:
#             raise ValueError("session_id cannot be empty")

#         if not isinstance(data, dict):
#             raise TypeError("data must be a dictionary")

#         # if "id" not in data:
#         #     raise KeyError("Dictionary must contain an 'id' field")

#         try:
#             if session_id not in self._store:
#                 self._store[session_id] = deque(maxlen=self.max_items)

#             self._store[session_id].append(data)
#             logger.info(
#                 "Dictionary added",
#                 extra={"session_id": session_id}
#             )

#         except Exception as e:
#             logger.exception("Failed to add dictionary")
#             raise RuntimeError("Failed to store dictionary") from e

#     # -----------------------------
#     # Retrieve dictionaries by ID
#     # -----------------------------
#     def get(
#         self,
#         session_id: str,
#         dict_id: Optional[str]
#     ) -> List[Dict]:
#         if not session_id:
#             raise ValueError("session_id cannot be empty")

#         # Requirement: empty dict_id → return empty list
#         if not dict_id:
#             return []

#         if session_id not in self._store:
#             return []

#         try:
#             return [
#                 item for item in self._store[session_id]
#                 if item.get("id") == dict_id
#             ]

#         except Exception as e:
#             logger.exception("Failed to retrieve dictionaries")
#             raise RuntimeError("Failed to retrieve dictionaries") from e

#     # -----------------------------
#     # Retrieve all latest dicts
#     # -----------------------------
#     def get_latest(
#         self,
#         session_id: str
#     ) -> List[Dict]:
#         if not session_id:
#             raise ValueError("session_id cannot be empty")

#         return list(self._store.get(session_id, []))
    
#     def get_all_items(self):
#         return self._store.items()
    
#     def get_all_keys(self) -> tuple:
#         return tuple(self._store.keys())

    

# # store = DictSessionStore()

# # # Add dictionaries
# # store.add("session-1", {"id": "a1", "value": 100})
# # store.add("session-1", {"id": "a2", "value": 200})
# # store.add("session-1", {"id": "a3", "value": 300})

# # # Retrieve by dict_id
# # print(store.get("session-1", "a2"))
# # # → [{'id': 'a2', 'value': 200}]

# # # Empty dict_id
# # print(store.get("session-1", None))
# # # → []

# # # Retrieve latest (max 5)
# # print(store.get_latest("session-1"))

from typing import Dict, List, Optional, Tuple
import logging
import json
import redis
from models.Response import Response
import os
from core.config import settings


logger = logging.getLogger(__name__)


class RedisDictSessionStore:
    def __init__(
        self,
        redis_url: str = settings.redis_url ,
        max_items: int = settings.max_items,              # ✅ N = 20
        ttl_seconds: int = settings.ttl_seconds ,           # ✅ TTL = 1 hour
        key_prefix: str = settings.redis_key_prefix
    ):
        self.max_items = max_items
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix

        try:
            self.redis = redis.Redis.from_url(
                redis_url,
                decode_responses=True
            )
            self.redis.ping()
        except Exception as e:
            logger.exception("Failed to connect to Redis")
            raise RuntimeError("Redis connection failed") from e

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _key(self, session_id: str) -> str:
        return f"{self.key_prefix}:{session_id}"

    # -----------------------------
    # Add dictionary to session
    # -----------------------------
    def add(
        self,
        session_id: str,
        data: Response
    ) -> None:
        if not session_id:
            raise ValueError("session_id cannot be empty")

        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")

        try:
            key = self._key(session_id)
            payload = json.dumps(data)

            pipe = self.redis.pipeline()
            pipe.lpush(key, payload)
            pipe.ltrim(key, 0, self.max_items - 1)
            pipe.expire(key, self.ttl_seconds)  # ✅ refresh TTL
            pipe.execute()

            logger.info(
                "Dictionary added",
                extra={"session_id": session_id}
            )

        except Exception as e:
            logger.exception("Failed to add dictionary")
            raise RuntimeError("Failed to store dictionary") from e

    # -----------------------------
    # Retrieve dictionaries by ID
    # -----------------------------
    def get(
        self,
        session_id: str,
        dict_id: Optional[str]
    ) -> List[Response]:
        if not session_id:
            raise ValueError("session_id cannot be empty")

        if not dict_id:
            return []

        key = self._key(session_id)

        try:
            items = self.redis.lrange(key, 0, -1)
            result = []

            for item in items:
                obj = json.loads(item)
                if obj.get("id") == dict_id:
                    result.append(obj)

            return result

        except Exception as e:
            logger.exception("Failed to retrieve dictionaries")
            raise RuntimeError("Failed to retrieve dictionaries") from e

    # -----------------------------
    # Retrieve all latest dicts
    # -----------------------------
    def get_latest(
        self,
        session_id: str
    ) -> List[Response]:
        if not session_id:
            raise ValueError("session_id cannot be empty")

        key = self._key(session_id)

        try:
            return [
                json.loads(item)
                for item in self.redis.lrange(key, 0, -1)
            ]
        except Exception as e:
            logger.exception("Failed to retrieve latest dictionaries")
            raise RuntimeError("Failed to retrieve latest dictionaries") from e

    # -----------------------------
    # Retrieve all items (admin/debug)
    # -----------------------------
    def get_all_items(self) -> List[Tuple[str, List[Response]]]:
        try:
            keys = self.redis.keys(f"{self.key_prefix}:*")
            result = []

            for key in keys:
                session_id = key.split(":", 1)[1]
                items = [
                    json.loads(item)
                    for item in self.redis.lrange(key, 0, -1)
                ]
                result.append((session_id, items))

            return result

        except Exception as e:
            logger.exception("Failed to retrieve all items")
            raise RuntimeError("Failed to retrieve all items") from e

    # -----------------------------
    # Retrieve all session keys
    # -----------------------------
    def get_all_keys(self) -> Tuple[str, ...]:
        try:
            keys = self.redis.keys(f"{self.key_prefix}:*")
            return tuple(key.split(":", 1)[1] for key in keys)

        except Exception as e:
            logger.exception("Failed to retrieve session keys")
            raise RuntimeError("Failed to retrieve session keys") from e
