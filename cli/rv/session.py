"""Remote viewing session engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ..data.rv_targets import RemoteViewingTarget
from ..utils.io import dump_json, ensure_directory, load_json, prompt_multiline

STAGES = (
    ("Stage 1 — Signal Line", "Capture immediate impressions without censoring."),
    ("Stage 2 — Sensory Expansion", "Describe textures, temperatures, sounds, and movements."),
    ("Stage 3 — Analytic Sketch", "Summarise structures, geometry, and notable features."),
)


@dataclass
class SessionRecord:
    target_id: str
    target_name: str
    started_at: str
    completed_at: str
    perceptions: Dict[str, List[str]]
    matches: List[str]
    accuracy: float


@dataclass
class RvSession:
    target: RemoteViewingTarget
    perceptions: Dict[str, List[str]] = field(default_factory=lambda: {stage: [] for stage, _ in STAGES})
    started_at: datetime = field(default_factory=datetime.utcnow)

    def record(self, stage_index: int) -> None:
        stage_name, prompt = STAGES[stage_index]
        responses = prompt_multiline(f"{stage_name}\n{prompt}\n")
        self.perceptions[stage_name].extend(responses)

    def score(self) -> tuple[list[str], float]:
        noted = {token.strip().lower() for values in self.perceptions.values() for token in values}
        matches = sorted({word for word in self.target.correct_elements if word.lower() in noted})
        accuracy = 0.0
        if self.target.correct_elements:
            accuracy = round(len(matches) / len(self.target.correct_elements) * 100, 2)
        return matches, accuracy

    def complete(self, storage: Path) -> SessionRecord:
        matches, accuracy = self.score()
        completed_at = datetime.utcnow()
        record = SessionRecord(
            target_id=self.target.target_id,
            target_name=self.target.name,
            started_at=self.started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            perceptions=self.perceptions,
            matches=matches,
            accuracy=accuracy,
        )
        ensure_directory(storage)
        history_path = storage / "rv-history.json"
        history = load_json(history_path, default={"sessions": []})
        history.setdefault("sessions", []).append(record.__dict__)
        dump_json(history_path, history)
        return record
