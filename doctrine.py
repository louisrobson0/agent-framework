import json
import os
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DoctrineEntry:
    principle: str
    learned_by: str
    context: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class Doctrine:
    def __init__(self, org_name: str):
        self.org_name = org_name
        self.path = f"{org_name.lower().replace(' ', '_')}_doctrine.json"
        self.entries: list[DoctrineEntry] = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path) as f:
                for e in json.load(f):
                    self.entries.append(DoctrineEntry(**e))

    def save(self):
        with open(self.path, "w") as f:
            json.dump([vars(e) for e in self.entries], f, indent=2)

    def add(self, entries: list[dict]):
        for e in entries:
            self.entries.append(DoctrineEntry(
                principle=e["principle"],
                learned_by=e.get("learned_by", "Organization"),
                context=e.get("context", ""),
            ))
        self.save()

    def to_context(self) -> str:
        if not self.entries:
            return ""
        lines = []
        for e in self.entries:
            line = f"• [{e.learned_by}] {e.principle}"
            if e.context:
                line += f" ({e.context})"
            lines.append(line)
        return "\n".join(lines)
