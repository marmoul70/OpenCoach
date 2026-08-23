from dataclasses import (
    asdict,
    dataclass,
)

from opencoach.planning.season.policy import (
    SeasonPlanningPolicy,
)
from opencoach.planning.season.strategist_context import (
    SeasonStrategistContext,
)
from opencoach.planning.season.strategist_port import (
    SeasonStrategistPort,
    SeasonStrategistResponse,
)
from opencoach.planning.season.strategist_request import (
    SeasonStrategistRequest,
    build_season_strategist_request,
)
from opencoach.planning.season.strategy_gate import (
    SeasonStrategyGateResult,
    evaluate_season_strategy_gate,
)
from opencoach.planning.season.strategy_parser import (
    parse_season_strategy_proposal,
)
from opencoach.planning.season.strategy_proposal import (
    SeasonStrategyProposal,
)


@dataclass(frozen=True)
class SeasonStrategistAttempt:
    """Trace d'une tentative individuelle du stratège IA."""

    attempt_number: int

    request: SeasonStrategistRequest

    response: SeasonStrategistResponse

    proposal: SeasonStrategyProposal

    gate: SeasonStrategyGateResult


@dataclass(frozen=True)
class SeasonStrategistExecution:
    """Trace complète d'une exécution du stratège IA.

    Une exécution peut contenir plusieurs tentatives lorsque
    le Gate Python demande une révision de la proposition.
    """

    attempts: tuple[
        SeasonStrategistAttempt,
        ...
    ]

    def __post_init__(self) -> None:
        if not self.attempts:
            raise ValueError(
                "Une exécution du stratège doit contenir "
                "au moins une tentative."
            )

    @property
    def attempt_count(self) -> int:
        return len(
            self.attempts
        )

    @property
    def final_attempt(
        self,
    ) -> SeasonStrategistAttempt:
        return self.attempts[-1]

    @property
    def request(
        self,
    ) -> SeasonStrategistRequest:
        """Conserve l'accès historique à la dernière requête."""

        return self.final_attempt.request

    @property
    def response(
        self,
    ) -> SeasonStrategistResponse:
        """Conserve l'accès historique à la dernière réponse."""

        return self.final_attempt.response

    @property
    def proposal(
        self,
    ) -> SeasonStrategyProposal:
        """Conserve l'accès historique à la dernière proposition."""

        return self.final_attempt.proposal

    @property
    def gate(
        self,
    ) -> SeasonStrategyGateResult:
        """Retourne la décision Python de la dernière tentative."""

        return self.final_attempt.gate

    @property
    def accepted(self) -> bool:
        return self.gate.accepted

    @property
    def requires_revision(self) -> bool:
        return self.gate.requires_revision

    @property
    def rejected(self) -> bool:
        return self.gate.rejected


class SeasonStrategistService:
    """Orchestre le stratège IA local et les garde-fous Python."""

    def __init__(
        self,
        *,
        strategist: SeasonStrategistPort,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError(
                "Le nombre maximal de tentatives "
                "doit être supérieur ou égal à 1."
            )

        self.strategist = strategist
        self.max_attempts = max_attempts

    def execute(
        self,
        *,
        context: SeasonStrategistContext,
        policy: SeasonPlanningPolicy,
    ) -> SeasonStrategistExecution:
        """Exécute le stratège jusqu'à validation ou épuisement.

        Seul un statut REVISE déclenche une nouvelle tentative.
        Une proposition acceptée, acceptée avec avertissements
        ou rejetée termine immédiatement l'exécution.
        """

        request = (
            build_season_strategist_request(
                context=context,
            )
        )

        attempts: list[
            SeasonStrategistAttempt
        ] = []

        for attempt_number in range(
            1,
            self.max_attempts + 1,
        ):
            response = self.strategist.generate(
                request=request,
            )

            proposal = (
                parse_season_strategy_proposal(
                    response.content
                )
            )

            gate = evaluate_season_strategy_gate(
                planning_input=(
                    context.planning_input
                ),
                proposal=proposal,
                policy=policy,
            )

            attempt = SeasonStrategistAttempt(
                attempt_number=attempt_number,
                request=request,
                response=response,
                proposal=proposal,
                gate=gate,
            )

            attempts.append(
                attempt
            )

            if not gate.requires_revision:
                break

            if attempt_number >= self.max_attempts:
                break

            request = _build_revision_request(
                previous_request=request,
                previous_proposal=proposal,
                gate=gate,
                next_attempt_number=(
                    attempt_number + 1
                ),
            )

        return SeasonStrategistExecution(
            attempts=tuple(
                attempts
            ),
        )


def _build_revision_request(
    *,
    previous_request: SeasonStrategistRequest,
    previous_proposal: SeasonStrategyProposal,
    gate: SeasonStrategyGateResult,
    next_attempt_number: int,
) -> SeasonStrategistRequest:
    """Construit une nouvelle requête contenant le feedback Python."""

    instructions = dict(
        previous_request.instructions
    )

    instructions[
        "revision_feedback"
    ] = {
        "attempt_number": (
            next_attempt_number
        ),
        "previous_proposal": (
            _serialize_previous_proposal(
                previous_proposal
            )
        ),
        "reasons": list(
            gate.reasons
        ),
        "instruction": (
            "Corriger la proposition précédente pour résoudre "
            "les violations signalées par le Gate Python. "
            "Conserver les parties conformes et modifier uniquement "
            "ce qui est nécessaire. "
            "Ne pas ignorer, contourner ou réinterpréter "
            "les contraintes."
        ),
    }

    return SeasonStrategistRequest(
        schema_version=(
            previous_request.schema_version
        ),
        planning=(
            previous_request.planning
        ),
        knowledge=(
            previous_request.knowledge
        ),
        instructions=instructions,
    )

def _serialize_previous_proposal(
    proposal: SeasonStrategyProposal,
) -> dict[str, object]:
    """Sérialise une proposition pour une demande de révision."""

    data = asdict(
        proposal
    )

    return _serialize_revision_value(
        data
    )


def _serialize_revision_value(
    value,
):
    """Convertit récursivement les valeurs métier en primitives JSON."""

    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if hasattr(
        value,
        "isoformat",
    ):
        return value.isoformat()

    if isinstance(
        value,
        tuple,
    ):
        return [
            _serialize_revision_value(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        list,
    ):
        return [
            _serialize_revision_value(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _serialize_revision_value(
                item
            )
            for key, item in value.items()
        }

    raise TypeError(
        "Type non sérialisable dans le feedback de révision: "
        f"{type(value).__name__}"
    )