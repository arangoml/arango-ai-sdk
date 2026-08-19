from enum import Enum


class TriggerRAGStrategizerRequestComplexity(str, Enum):
    HIGH = "high"
    LOW = "low"
    MODERATE = "moderate"
    VERY_HIGH = "very_high"
    VERY_LOW = "very_low"

    def __str__(self) -> str:
        return str(self.value)
