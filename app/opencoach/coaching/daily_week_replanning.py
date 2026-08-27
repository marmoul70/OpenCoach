"""Coordination des replanifications quotidiennes à l'échelle de la semaine.

Le moteur individuel sait proposer plusieurs choix pour une séance annulée.

Ce module coordonne plusieurs séances annulées le même jour afin que
les recommandations OpenCoach restent cohérentes entre elles.

Il ne persiste aucune modification.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from opencoach.coaching.daily_session_replanning import (
    DailyReplanningAction,
    DailySessionReplanningOption,
    DailySessionReplanningProposal,
)


@dataclass(
    frozen=True,
    slots=True,
)
class DailyWeekReplanningDecision:
    """Décision recommandée pour une séance annulée."""

    proposal: DailySessionReplanningProposal

    recommended_option: DailySessionReplanningOption


@dataclass(
    frozen=True,
    slots=True,
)
class DailyWeekReplanningPlan:
    """Recommandation globale OpenCoach."""

    decisions: tuple[
        DailyWeekReplanningDecision,
        ...,
    ]

    reasons: tuple[
        str,
        ...,
    ]

    @property
    def recommended_dates(
        self,
    ) -> tuple[
        date,
        ...,
    ]:
        """Dates réellement utilisées par les reports recommandés."""

        return tuple(
            decision.recommended_option.target_date
            for decision in self.decisions
            if (
                decision.recommended_option.target_date
                is not None
            )
        )


def coordinate_daily_week_replanning(
    *,
    proposals: tuple[
        DailySessionReplanningProposal,
        ...,
    ],
) -> DailyWeekReplanningPlan:
    """Coordonne plusieurs propositions individuelles.

    Règle V1 :

    - une seule séance annulée peut être recommandée sur un même jour ;
    - les séances d'endurance sont prioritaires sur le renforcement
      lorsqu'elles se disputent le même créneau ;
    - lorsqu'une collision existe, les autres séances sont annulées
      dans la recommandation globale ;
    - toutes les options restent disponibles à l'athlète.

    Cette fonction ne modifie pas les propositions individuelles.
    """

    if not proposals:
        return DailyWeekReplanningPlan(
            decisions=(),
            reasons=(),
        )

    ordered = tuple(
        sorted(
            proposals,
            key=_proposal_priority,
        )
    )

    occupied_replanning_dates: set[
        date
    ] = set()

    decisions: list[
        DailyWeekReplanningDecision
    ] = []

    reasons: list[str] = []

    for proposal in ordered:
        individual = (
            proposal.recommended_option
        )

        chosen = individual

        target_date = (
            individual.target_date
        )

        if (
            target_date is not None
            and target_date
            in occupied_replanning_dates
        ):
            chosen = (
                _cancel_option(
                    proposal
                )
            )

            reasons.append(
                (
                    f"{proposal.original_session.title} : "
                    "annulation recommandée afin d'éviter "
                    f"plusieurs séances reportées le "
                    f"{target_date.isoformat()}."
                )
            )

        elif target_date is not None:
            occupied_replanning_dates.add(
                target_date
            )

        decisions.append(
            DailyWeekReplanningDecision(
                proposal=proposal,
                recommended_option=(
                    chosen
                ),
            )
        )

    if (
        len(proposals) > 1
        and occupied_replanning_dates
    ):
        reasons.insert(
            0,
            (
                "OpenCoach coordonne les séances annulées "
                "afin de répartir la charge restante sans "
                "créer artificiellement un cumul."
            ),
        )

    # L'ordre final reste celui des séances sources.
    decisions.sort(
        key=lambda decision: (
            decision
            .proposal
            .original_session
            .date,
            str(
                decision
                .proposal
                .original_session
                .id
            ),
        )
    )

    return DailyWeekReplanningPlan(
        decisions=tuple(
            decisions
        ),
        reasons=tuple(
            reasons
        ),
    )


def _proposal_priority(
    proposal: DailySessionReplanningProposal,
) -> tuple[
    int,
    int,
    str,
]:
    """Classe les séances pour résoudre les collisions.

    Une séance de course conserve davantage de valeur spécifique
    qu'un renforcement court lorsque les deux doivent être reportés
    sur le même créneau.
    """

    session = (
        proposal.original_session
    )

    session_type = (
        session.type
        .strip()
        .lower()
    )

    sport_type = (
        session.sport_type
        .strip()
        .lower()
    )

    is_strength = (
        session_type.startswith(
            "strength"
        )
        or sport_type
        in {
            "strength",
            "musculation",
        }
    )

    modality_priority = (
        1
        if is_strength
        else 0
    )

    duration_priority = -(
        session.duration_minutes
        or 0
    )

    return (
        modality_priority,
        duration_priority,
        str(
            session.id
        ),
    )


def _cancel_option(
    proposal: DailySessionReplanningProposal,
) -> DailySessionReplanningOption:
    """Retourne l'option d'annulation de la proposition."""

    option = next(
        (
            option
            for option in proposal.options
            if (
                option.action
                is DailyReplanningAction.CANCEL
            )
        ),
        None,
    )

    if option is None:
        raise RuntimeError(
            "Une proposition de replanification "
            "doit toujours contenir l'annulation."
        )

    return replace(
        option,
        recommended=True,
        reasons=(
            *option.reasons,
            (
                "OpenCoach recommande cette option "
                "dans l'équilibre global de la semaine."
            ),
        ),
    )
