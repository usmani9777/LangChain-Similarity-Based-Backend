from pydantic import BaseModel,Field
from typing import Optional
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from datetime import date

y
MemoryType = Literal["Personal", "Goal", "Fact"]


class Memory(BaseModel):
    """
    Memory represents a single persistent unit of user knowledge used by
    conversational agents, RAG systems, or long-term memory stores.

    Each memory:
    - Belongs to a user and session
    - Has a semantic type (Personal, Goal, Fact)
    - Tracks creation and access timestamps
    - Computes an importance score automatically

    Importance is derived from:
    1. Memory type (Goal > Personal > Fact)
    2. Age of the memory (older memories decay)
    3. Recency of access (recently accessed memories are boosted)

    The importance score is normalized between 0.0 and 1.0 and is suitable for:
    - Memory retrieval ranking
    - Context pruning
    - RAG or agent memory selection
    """
    user_id: Optional[str] = Field( None, min_length=4, description="User identifier"    )
    session_id: str = Field(...,min_length=10,max_length=20,description="Session identifier")
    memory_type: MemoryType = Field(...,description="Type of memory")
    text: str = Field(...,min_length=5,max_length=1000,description="Memory content")
    created_date: date = Field(default_factory=date.today,description="Date memory was created")
    last_accessed: date = Field(default_factory=date.today,description="Last accessed date")
    importance: float = Field(0.0,ge=0.0,le=1.0,description="Computed importance score (0–1)")

    @model_validator(mode="after")
    def compute_importance(self) -> "Memory":
        today = date.today()

        # 1️⃣ Base importance by type
        type_weight = {
            "Personal": 0.9,
            "Goal": 1.0,
            "Fact": 0.6
        }[self.memory_type]

        # 2️⃣ Time decay (older memories decay)
        days_since_created = max((today - self.created_date).days, 0)
        created_decay = max(0.3, 1 - (days_since_created / 365))

        # 3️⃣ Access boost (recently used memories matter more)
        days_since_access = max((today - self.last_accessed).days, 0)
        access_boost = max(0.5, 1 - (days_since_access / 30))

        # 4️⃣ Final importance score
        self.importance = round(
            type_weight * created_decay * access_boost,
            3
        )

        return self
