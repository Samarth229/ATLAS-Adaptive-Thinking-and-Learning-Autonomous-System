from abc import ABC, abstractmethod


class BaseToolV0_1(ABC):

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, input_data: dict) -> dict:
        """
        Returns:
        {
            "success": bool,
            "output": any,
            "error": str | None
        }
        """
        pass