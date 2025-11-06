"""Static research archive content."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Literal

from .user import TierLevel

Category = Literal["research", "operational", "training", "general"]


@dataclass(frozen=True)
class ResearchDocument:
    id: str
    document_id: str
    title: str
    content: str
    classification: str
    access_level: TierLevel
    file_type: str
    file_size: int
    category: Category
    tags: tuple[str, ...]
    author: str
    summary: str
    created_at: datetime


DOCUMENTS: tuple[ResearchDocument, ...] = (
    ResearchDocument(
        id="cc-defensive-strategies-001",
        document_id="cc-defensive-strategies-001",
        title="Analyzing Citizen Cipher's Defensive Strategies",
        content=(
            "A deep dive into the Citizen Cipher curriculum's KSAO framework, bias targeting mechanisms, and verification"
            " architectures for defensive proficiency."
        ),
        classification="RESEARCH ARCHIVE",
        access_level="beta",
        file_type="md",
        file_size=18_432,
        category="research",
        tags=("cognitive-biases", "defensive-strategies", "verification"),
        author="Citizen Cipher Research Team",
        summary="Deep-dive analysis of defensive countermeasures that harden perception, decision-making, and verification workflows.",
        created_at=datetime.fromisoformat("2024-01-05T00:00:00+00:00"),
    ),
    ResearchDocument(
        id="cc-brand-identity-001",
        document_id="cc-brand-identity-001",
        title="Designing Brand Identity and PR Kit for Citizen Cipher",
        content=(
            "Strategic launch architecture for external visual identity and public relations kit built on design psychology and"
            " zero-trust principles."
        ),
        classification="OPERATIONAL",
        access_level="beta",
        file_type="md",
        file_size=14_208,
        category="operational",
        tags=("branding", "marketing", "psychology"),
        author="Citizen Cipher Marketing Division",
        summary="Launch playbook covering narrative framing, trust scaffolding, and psychological signaling for the Citizen Cipher platform.",
        created_at=datetime.fromisoformat("2024-01-10T00:00:00+00:00"),
    ),
    ResearchDocument(
        id="cc-historic-heists-001",
        document_id="cc-historic-heists-001",
        title="Historic Heists: Psychological Breakdown",
        content=(
            "Forensic analysis of historic deception operations with emphasis on cognitive openings, bias exploitation, and defensive"
            " countermeasures."
        ),
        classification="RESEARCH ARCHIVE",
        access_level="beta",
        file_type="md",
        file_size=20_992,
        category="research",
        tags=("case-studies", "social-engineering", "analysis"),
        author="Citizen Cipher Research Team",
        summary="Forensic profiles of high-yield attacks mapped to defensive countermeasures and verification protocols.",
        created_at=datetime.fromisoformat("2024-01-18T00:00:00+00:00"),
    ),
    ResearchDocument(
        id="cc-persuasive-heuristics-001",
        document_id="cc-persuasive-heuristics-001",
        title="Persuasion, Biases, and Game Theory",
        content=(
            "Game-theoretic framework synthesising behavioral economics, social psychology, and persuasion tactics for cognitive hardening."
        ),
        classification="RESEARCH ARCHIVE",
        access_level="theta",
        file_type="md",
        file_size=17_664,
        category="research",
        tags=("persuasion", "game-theory", "heuristics"),
        author="Citizen Cipher Research Team",
        summary="Extended exploration of bias exploitation patterns with counter-bias conditioning exercises.",
        created_at=datetime.fromisoformat("2024-01-22T00:00:00+00:00"),
    ),
    ResearchDocument(
        id="cc-podcast-offensive-001",
        document_id="cc-podcast-offensive-001",
        title="Podcast Scripting for Offensive Defense",
        content=(
            "Voice operations blueprint translating research-grade doctrine into high-fidelity broadcast scripts for cognitive priming."
        ),
        classification="OPERATIONAL",
        access_level="alpha",
        file_type="md",
        file_size=12_256,
        category="operational",
        tags=("audio", "content", "pedagogy"),
        author="Citizen Cipher Media Division",
        summary="Script architecture for mission briefings, cadence patterns, and mental imagery reinforcement.",
        created_at=datetime.fromisoformat("2024-01-28T00:00:00+00:00"),
    ),
    ResearchDocument(
        id="cc-project-blueprint-ii-001",
        document_id="cc-project-blueprint-ii-001",
        title="Project Blueprint II: Grid Expansion & Systemic Resilience",
        content=(
            "Advanced operational security protocols covering cognitive hardening, digital ghost operations, and resilient archive design."
        ),
        classification="OPERATIONAL - CLASSIFIED",
        access_level="gamma",
        file_type="md",
        file_size=24_576,
        category="operational",
        tags=("opsec", "resilience", "shadow-state"),
        author="Omega Integration Protocol",
        summary="High-tier operational blueprint for maintaining continuity under contested environments.",
        created_at=datetime.fromisoformat("2024-02-02T00:00:00+00:00"),
    ),
)


def iter_by_tier(tier: TierLevel) -> Iterable[ResearchDocument]:
    tier_order = {"none": 0, "alpha": 1, "beta": 2, "theta": 3, "gamma": 4}
    threshold = tier_order[tier]
    for document in DOCUMENTS:
        if tier_order[document.access_level] <= threshold:
            yield document
