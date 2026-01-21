from enum import Enum

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

        self.fact_patterns = [
            "remember", "my", "expires", "was born", "is my", "my email"
        ]

    def classify(self, text: str) -> MemoryType | None:
        text = text.lower()

        if any(p in text for p in self.goal_patterns):
            return MemoryType.GOAL

        if any(p in text for p in self.personal_patterns):
            return MemoryType.PERSONAL

        if any(p in text for p in self.fact_patterns):
            return MemoryType.FACT

        return None
