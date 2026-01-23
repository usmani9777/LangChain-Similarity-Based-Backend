# from enum import Enum

# class MemoryType(str, Enum):
#     GOAL = "Goal"
#     PERSONAL = "Personal"
#     FACT = "Fact"
    
# class RuleBasedMemoryClassifier:
#     def __init__(self):
#         self.goal_patterns = [
#             "i want", "i plan", "i need", "my goal", "i aim", "i will"
#         ]

#         self.personal_patterns = [
#             "i am", "i like", "i prefer", "i enjoy", "i hate", "i love"
#         ]

#         self.fact_patterns = [
#             "remember", "my", "expires", "was born", "is my", "my email"
#         ]

#     def classify(self, text: str) -> MemoryType | None:
#         text = text.lower()

#         if any(p in text for p in self.goal_patterns):
#             return MemoryType.GOAL

#         if any(p in text for p in self.personal_patterns):
#             return MemoryType.PERSONAL

#         if any(p in text for p in self.fact_patterns):
#             return MemoryType.FACT

#         return None


from enum import Enum
from typing import Optional
import spacy 
nlp = spacy.load("en_core_web_sm")

class MemoryType(str, Enum):
    GOAL = "Goal"
    PERSONAL = "Personal"
    FACT = "Fact"


class RuleBasedMemoryClassifier:
    def __init__(self):
        self.goal_patterns = [
            "i want", "i plan", "i need", "my goal", "i aim", "i will"
        ]

        self.personal_patterns = [
            "i am", "i like", "i prefer", "i enjoy", "i hate", "i love"
        ]

    def _detect_goal_intent(self, text: str) -> bool:
        return any(p in text for p in self.goal_patterns)

    def _detect_personal_intent(self, text: str) -> bool:
        return any(p in text for p in self.personal_patterns)

    def _detect_entities(self, text: str) -> dict:
        doc = nlp(text)
        entities = {
            "PERSON": [],
            "GPE": [],
            "ORG": [],
            "DATE": [],
            "EMAIL": []
        }

        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text)

        return entities

    def classify(self, text: str) -> Optional[MemoryType]:
        text_lower = text.lower()

        # 1️⃣ Intent-based detection
        if self._detect_goal_intent(text_lower):
            return MemoryType.GOAL

        if self._detect_personal_intent(text_lower):
            return MemoryType.PERSONAL

        # 2️⃣ Entity-based detection
        entities = self._detect_entities(text)

        if any(entities.values()):
            return MemoryType.FACT

        return None
