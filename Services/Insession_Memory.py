from collections import deque
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DictSessionStore:
    def __init__(self, max_items: int = 5):
        self.max_items = max_items
        self._store: Dict[str, deque] = {}

    # -----------------------------
    # Add dictionary to session
    # -----------------------------
    def add(
        self,
        session_id: str,
        data: Dict
    ) -> None:
        if not session_id:
            raise ValueError("session_id cannot be empty")

        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")

        # if "id" not in data:
        #     raise KeyError("Dictionary must contain an 'id' field")

        try:
            if session_id not in self._store:
                self._store[session_id] = deque(maxlen=self.max_items)

            self._store[session_id].append(data)
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
    ) -> List[Dict]:
        if not session_id:
            raise ValueError("session_id cannot be empty")

        # Requirement: empty dict_id → return empty list
        if not dict_id:
            return []

        if session_id not in self._store:
            return []

        try:
            return [
                item for item in self._store[session_id]
                if item.get("id") == dict_id
            ]

        except Exception as e:
            logger.exception("Failed to retrieve dictionaries")
            raise RuntimeError("Failed to retrieve dictionaries") from e

    # -----------------------------
    # Retrieve all latest dicts
    # -----------------------------
    def get_latest(
        self,
        session_id: str
    ) -> List[Dict]:
        if not session_id:
            raise ValueError("session_id cannot be empty")

        return list(self._store.get(session_id, []))


# store = DictSessionStore()

# # Add dictionaries
# store.add("session-1", {"id": "a1", "value": 100})
# store.add("session-1", {"id": "a2", "value": 200})
# store.add("session-1", {"id": "a3", "value": 300})

# # Retrieve by dict_id
# print(store.get("session-1", "a2"))
# # → [{'id': 'a2', 'value': 200}]

# # Empty dict_id
# print(store.get("session-1", None))
# # → []

# # Retrieve latest (max 5)
# print(store.get_latest("session-1"))
