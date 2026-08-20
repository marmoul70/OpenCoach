from dataclasses import dataclass
from typing import Literal

from .recent_load import RecentTrainingLoad


RecentLoadSignalLevel = Literal[
    "info",
    "warning",
    "critical",
]


RecentLoadSignalKind = Literal[
    "recent_overload",
    "repeated_overload",
    "broken_rest",
    "repeated_broken_rest",
]


@dataclass(frozen=True)
class RecentLoadSignal:
    """Signal dérivé de la charge récente."""

    kind: RecentLoadSignalKind
    level: RecentLoadSignalLevel
    reason: str


@dataclass(frozen=True)
class RecentLoadAssessment:
    """Synthèse des signaux issus de l'historique récent."""

    signals: tuple[
        RecentLoadSignal,
        ...,
    ]

    @property
    def has_warning(self) -> bool:
        return any(
            signal.level == "warning"
            for signal in self.signals
        )

    @property
    def has_critical(self) -> bool:
        return any(
            signal.level == "critical"
            for signal in self.signals
        )

    @property
    def has_overload(self) -> bool:
        return any(
            signal.kind
            in {
                "recent_overload",
                "repeated_overload",
            }
            for signal in self.signals
        )

    @property
    def has_broken_rest(self) -> bool:
        return any(
            signal.kind
            in {
                "broken_rest",
                "repeated_broken_rest",
            }
            for signal in self.signals
        )


def assess_recent_training_load(
    recent_load: RecentTrainingLoad,
) -> RecentLoadAssessment:
    """Transforme l'historique de charge en signaux métier."""

    signals: list[
        RecentLoadSignal
    ] = []

    if not recent_load.days:
        return RecentLoadAssessment(
            signals=(),
        )

    latest_day = (
        recent_load.days[0]
    )

    if latest_day.status == "above_plan":
        signals.append(
            RecentLoadSignal(
                kind="recent_overload",
                level="warning",
                reason=(
                    "La charge réalisée hier était "
                    "supérieure au programme prévu."
                ),
            )
        )

    if (
        recent_load.above_plan_days
        >= 2
    ):
        signals.append(
            RecentLoadSignal(
                kind="repeated_overload",
                level="critical",
                reason=(
                    "La charge a dépassé le programme "
                    "sur plusieurs jours récents."
                ),
            )
        )

    if latest_day.status == "rest_broken":
        signals.append(
            RecentLoadSignal(
                kind="broken_rest",
                level="warning",
                reason=(
                    "Une activité sportive a été réalisée "
                    "hier malgré une journée de repos prévue."
                ),
            )
        )

    if (
        recent_load.broken_rest_days
        >= 2
    ):
        signals.append(
            RecentLoadSignal(
                kind="repeated_broken_rest",
                level="critical",
                reason=(
                    "Plusieurs journées de repos récentes "
                    "ont comporté une charge sportive."
                ),
            )
        )

    return RecentLoadAssessment(
        signals=tuple(
            signals,
        ),
    )
