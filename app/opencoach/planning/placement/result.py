from dataclasses import dataclass

from opencoach.planning.placement.scoring import (
    SessionPlacementCandidate,
)


@dataclass(frozen=True)
class SessionPlacementResult:
    """Résultat structuré de la recherche d'un placement."""

    eligible_candidates: tuple[
        SessionPlacementCandidate,
        ...
    ]

    rejected_candidates: tuple[
        SessionPlacementCandidate,
        ...
    ]

    @property
    def best_candidate(
        self,
    ) -> SessionPlacementCandidate | None:
        """Retourne le meilleur candidat éligible."""

        if not self.eligible_candidates:
            return None

        return self.eligible_candidates[0]

    @property
    def has_solution(self) -> bool:
        """Indique si au moins un placement valide existe."""

        return bool(
            self.eligible_candidates
        )


def build_session_placement_result(
    candidates: tuple[
        SessionPlacementCandidate,
        ...
    ],
) -> SessionPlacementResult:
    """Sépare les candidats valides des candidats rejetés."""

    eligible_candidates = tuple(
        candidate
        for candidate in candidates
        if candidate.eligible
    )

    rejected_candidates = tuple(
        candidate
        for candidate in candidates
        if not candidate.eligible
    )

    return SessionPlacementResult(
        eligible_candidates=eligible_candidates,
        rejected_candidates=rejected_candidates,
    )
