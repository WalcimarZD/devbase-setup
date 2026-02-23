from dataclasses import dataclass
from typing import Callable, Optional
from pathlib import Path

@dataclass
class HealthIssue:
    description: str
    fix_action: Optional[Callable] = None
    fix_description: str = "Manual fix required"

class BaseCheck:
    def __init__(self, root: Path):
        self.root = root

    def run(self) -> list[HealthIssue]:
        raise NotImplementedError
