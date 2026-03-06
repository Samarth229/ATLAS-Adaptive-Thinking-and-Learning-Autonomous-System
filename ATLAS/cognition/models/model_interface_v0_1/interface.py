from abc import ABC, abstractmethod


class ModelInterfaceV0_1(ABC):

    @abstractmethod
    def generate(self, prompt: str, context: dict = None) -> dict:
        """
        Returns:
        {
            "text": str,
            "confidence": float,
            "meta": dict
        }
        """
        pass