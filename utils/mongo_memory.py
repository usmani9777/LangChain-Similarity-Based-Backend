from pymongo import MongoClient
from datetime import date
from typing import List, Optional
from core.config import settings

class MongoMemoryStore:
    def __init__(
        self,
        mongo_uri: str,
        db_name: str = settings.mongo_db_name,
        collection_name: str = settings.mongo_collection_name
    ):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

        self._create_indexes()

    def _create_indexes(self):
        self.collection.create_index("user_id")
        self.collection.create_index("memory_type")
        self.collection.create_index("importance")

    # -------------------------
    # ADD MEMORY
    # -------------------------
    def add_memory(self, memory: dict) -> str:
        result = self.collection.insert_one(memory)
        return str(result.inserted_id)

    # -------------------------
    # RETRIEVE BY TYPE
    # -------------------------
    def get_memories_by_type(
        self,
        user_id: str,
        memory_type: str,
        limit: int = 5
    ) -> List[dict]:
        return list(
            self.collection.find(
                {"user_id": user_id, "memory_type": memory_type}
            )
            .sort("importance", -1)
            .limit(limit)
        )

    # -------------------------
    # UPDATE ACCESS TIME
    # -------------------------
    def update_access(self, memory_id):
        self.collection.update_one(
            {"_id": memory_id},
            {"$set": {"last_accessed": date.today()}}
        )

    # -------------------------
    # DELETE LOW IMPORTANCE
    # -------------------------
    def prune_memories(self, threshold: float = 0.2):
        self.collection.delete_many(
            {"importance": {"$lt": threshold}}
        )
