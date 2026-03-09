"""Memory-based learning system for continual improvement.

This module provides a generic memory abstraction for recording and applying
lessons learned from previous trajectories. The initial implementation follows
Dynamic Cheatsheet (Suzgun et al 2025), but the architecture supports
alternative memory implementations (e.g., retrieval-augmented, structured).
"""

from .base import MemoryModule, MemoryUpdater
from .cheatsheet import CheatsheetMemory, CheatsheetUpdater

__all__ = [
    "MemoryModule",
    "MemoryUpdater",
    "CheatsheetMemory",
    "CheatsheetUpdater",
]
