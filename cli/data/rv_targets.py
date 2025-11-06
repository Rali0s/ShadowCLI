"""Remote viewing target catalog."""

from __future__ import annotations

from dataclasses import dataclass
from random import choice
from typing import Iterable, Literal, Sequence

RvDifficulty = Literal["novice", "intermediate", "advanced"]
RvCategory = Literal["geographic", "structure", "object", "symbol"]


@dataclass(frozen=True)
class RemoteViewingTarget:
    id: str
    target_id: str
    name: str
    description: str
    category: RvCategory
    difficulty: RvDifficulty
    correct_elements: tuple[str, ...]


TARGETS: tuple[RemoteViewingTarget, ...] = (
    RemoteViewingTarget(
        id="rv-target-001",
        target_id="2031-ALPHA",
        name="Washington Monument",
        description="Tall marble obelisk within a landscaped park and reflecting pool.",
        category="structure",
        difficulty="novice",
        correct_elements=("obelisk", "stone", "tall", "monument", "reflecting pool", "washington"),
    ),
    RemoteViewingTarget(
        id="rv-target-002",
        target_id="5072-BETA",
        name="Stonehenge",
        description="Circular arrangement of massive standing stones under open sky.",
        category="geographic",
        difficulty="novice",
        correct_elements=("stones", "circle", "ancient", "field", "monolith"),
    ),
    RemoteViewingTarget(
        id="rv-target-003",
        target_id="7410-THETA",
        name="Santorini Caldera",
        description="Cliffside island village overlooking a blue volcanic caldera.",
        category="geographic",
        difficulty="intermediate",
        correct_elements=("water", "cliff", "island", "white buildings", "caldera"),
    ),
    RemoteViewingTarget(
        id="rv-target-004",
        target_id="9923-GAMMA",
        name="Yin Yang Symbol",
        description="Black and white circular glyph representing balance and duality.",
        category="symbol",
        difficulty="intermediate",
        correct_elements=("circle", "black", "white", "symbol", "balance"),
    ),
    RemoteViewingTarget(
        id="rv-target-005",
        target_id="8844-PHI",
        name="International Space Station",
        description="Modular spacecraft orbiting Earth with solar panel arrays.",
        category="structure",
        difficulty="advanced",
        correct_elements=("space", "station", "solar panels", "orbit", "metal"),
    ),
)


def filter_targets(*, difficulty: RvDifficulty | None = None) -> Sequence[RemoteViewingTarget]:
    if difficulty is None:
        return TARGETS
    return tuple(target for target in TARGETS if target.difficulty == difficulty)


def choose_target(*, difficulty: RvDifficulty | None = None) -> RemoteViewingTarget:
    candidates = filter_targets(difficulty=difficulty)
    return choice(candidates)


def list_categories(targets: Iterable[RemoteViewingTarget]) -> set[RvCategory]:
    return {target.category for target in targets}
