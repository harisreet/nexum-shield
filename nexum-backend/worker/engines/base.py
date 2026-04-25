"""
NEXUM SHIELD — Engine Abstract Base Class
All engines follow this contract: process(input: dict) -> dict.
No cross-engine coupling. Pure, stateless transformations.
"""
from abc import ABC, abstractmethod
from typing import Any


class Engine(ABC):
    """
    Base class for all NEXUM SHIELD pipeline engines.

    Rules:
    - Each engine is pure: same input always produces same output.
    - No engine may depend on another engine directly.
    - All inputs and outputs must be serializable dicts.
    - Engines must not perform I/O (use services for that).
    """

    @abstractmethod
    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the engine's transformation.

        Args:
            input_data: Engine-specific input dict. Schema defined per engine.

        Returns:
            Engine-specific output dict. Schema defined per engine.

        Raises:
            EngineError: If processing fails. Never swallow errors silently.
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.__class__.__name__


class EngineError(Exception):
    """Raised when an engine encounters an unrecoverable error."""

    def __init__(self, engine: str, message: str, original: Exception | None = None):
        self.engine = engine
        self.original = original
        super().__init__(f"[{engine}] {message}")
