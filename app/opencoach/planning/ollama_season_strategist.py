import json
from dataclasses import dataclass
from urllib.error import (
    HTTPError,
    URLError,
)
from urllib.request import (
    Request,
    urlopen,
)

from .season_strategist_port import (
    SeasonStrategistInvalidResponseError,
    SeasonStrategistPort,
    SeasonStrategistResponse,
    SeasonStrategistUnavailableError,
)
from .season_strategist_request import (
    SeasonStrategistRequest,
)
from .season_strategy_schema import (
    build_season_strategy_proposal_schema,
)

@dataclass(frozen=True)
class OllamaSeasonStrategistConfig:
    """Configuration du moteur Ollama local."""

    base_url: str = "http://127.0.0.1:11434"

    model: str = ""

    timeout_seconds: float = 120.0

    temperature: float = 0.2

    def __post_init__(self) -> None:
        if not self.base_url.strip():
            raise ValueError(
                "L'URL Ollama ne peut pas être vide."
            )

        if not self.model.strip():
            raise ValueError(
                "Le modèle Ollama ne peut pas être vide."
            )

        if self.timeout_seconds <= 0:
            raise ValueError(
                "Le timeout Ollama doit être positif."
            )

        if self.temperature < 0:
            raise ValueError(
                "La température Ollama ne peut pas être négative."
            )


class OllamaSeasonStrategist(
    SeasonStrategistPort
):
    """Adapter local vers l'API HTTP Ollama."""

    def __init__(
        self,
        *,
        config: OllamaSeasonStrategistConfig,
    ) -> None:
        self.config = config

    def generate(
        self,
        *,
        request: SeasonStrategistRequest,
    ) -> SeasonStrategistResponse:
        payload = _build_ollama_payload(
            request=request,
            config=self.config,
        )

        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode(
            "utf-8"
        )

        http_request = Request(
            url=(
                self.config.base_url.rstrip("/")
                + "/api/chat"
            ),
            data=body,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(
                http_request,
                timeout=self.config.timeout_seconds,
            ) as response:
                raw_body = response.read()

        except HTTPError as exc:
            raise SeasonStrategistUnavailableError(
                f"Ollama a retourné HTTP {exc.code}."
            ) from exc

        except (
            URLError,
            TimeoutError,
            ConnectionError,
        ) as exc:
            raise SeasonStrategistUnavailableError(
                "Ollama local n'est pas disponible."
            ) from exc

        except (
            URLError,
            TimeoutError,
            ConnectionError,
        ) as exc:
            raise SeasonStrategistUnavailableError(
                "Ollama local n'est pas disponible."
            ) from exc
        except HTTPError as exc:
            raise SeasonStrategistUnavailableError(
                f"Ollama a retourné HTTP {exc.code}."
            ) from exc

        try:
            response_payload = json.loads(
                raw_body.decode(
                    "utf-8"
                )
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise SeasonStrategistInvalidResponseError(
                "La réponse HTTP Ollama n'est pas un JSON valide."
            ) from exc

        return _parse_ollama_response(
            response_payload
        )


def _build_ollama_payload(
    *,
    request: SeasonStrategistRequest,
    config: OllamaSeasonStrategistConfig,
) -> dict[str, object]:

    schema = (
        build_season_strategy_proposal_schema()
    )

    strategist_payload = {
        "schema_version": request.schema_version,
        "planning": request.planning,
        "knowledge": request.knowledge,
        "instructions": request.instructions,
    }

    prompt = json.dumps(
        strategist_payload,
        ensure_ascii=False,
    )

    return {
        "model": config.model,
        "stream": False,
        "format": schema,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Tu es le stratège d'entraînement OpenCoach. "
                    "Produis uniquement une proposition stratégique JSON. "
                    "N'ajoute aucun texte avant ou après le JSON. "
                    "Respecte strictement le JSON Schema suivant : "
                    + json.dumps(
                        schema,
                        ensure_ascii=False,
                    )
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "options": {
            "temperature": config.temperature,
        },
    }


def _parse_ollama_response(
    response_payload: object,
) -> SeasonStrategistResponse:
    if not isinstance(
        response_payload,
        dict,
    ):
        raise SeasonStrategistInvalidResponseError(
            "La réponse Ollama doit être un objet JSON."
        )

    message = response_payload.get(
        "message"
    )

    if not isinstance(
        message,
        dict,
    ):
        raise SeasonStrategistInvalidResponseError(
            "La réponse Ollama ne contient pas de message."
        )

    content = message.get(
        "content"
    )

    if not isinstance(
        content,
        str,
    ):
        raise SeasonStrategistInvalidResponseError(
            "Le contenu Ollama est absent ou invalide."
        )

    try:
        structured_content = json.loads(
            content
        )
    except json.JSONDecodeError as exc:
        raise SeasonStrategistInvalidResponseError(
            "Le contenu produit par Ollama n'est pas un JSON valide."
        ) from exc

    if not isinstance(
        structured_content,
        dict,
    ):
        raise SeasonStrategistInvalidResponseError(
            "Le contenu stratégique doit être un objet JSON."
        )

    model = response_payload.get(
        "model"
    )

    if not isinstance(
        model,
        str,
    ):
        model = None

    return SeasonStrategistResponse(
        content=structured_content,
        model=model,
        raw_response=response_payload,
    )
