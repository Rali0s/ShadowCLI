"""Demo user profile mirroring the web experience."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TierLevel = Literal["none", "alpha", "beta", "theta", "gamma"]


@dataclass(frozen=True)
class DemoUser:
    id: str
    email: str | None
    subscription_status: Literal["active", "inactive", "trial", "cancelled"]
    subscription_tier: TierLevel
    discord_username: str
    first_name: str | None
    last_name: str | None


DEMO_USER = DemoUser(
    id="demo-user",
    email=None,
    subscription_status="active",
    subscription_tier="gamma",
    discord_username="ShadowOpsDemo",
    first_name="Shadow",
    last_name="Operative",
)
