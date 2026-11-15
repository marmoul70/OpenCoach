import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ai.evaluate_coaching_responses import score_coaching_response


FIXTURE = ROOT / "tests" / "fixtures" / "ai_coaching_data_quality_cases.json"


def case():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))[0]


def test_stale_readiness_and_partial_history_require_fresh_context():
    item = case()
    good = (
        "Ta Readiness est périmée : la dernière mesure date du 10/11/2026. "
        "L'historique d'entraînement est partiel, donc je ne peux pas confirmer "
        "ta charge réelle ; synchronise tes séances et donne-moi ton ressenti récent "
        "avant de décider si tu maintiens le tempo."
    )
    result = score_coaching_response(item, good)
    assert result["checks"]["action_pass"] is True
    assert result["checks"]["data_quality_pass"] is True
    assert result["pass"] is True


def test_stale_readiness_must_be_explicitly_dated():
    item = case()
    response = (
        "Ta Readiness semble ancienne et l'historique est partiel. "
        "Synchronise tes données récentes et indique ton ressenti actuel "
        "avant de décider pour demain."
    )
    result = score_coaching_response(item, response)
    assert result["checks"]["data_quality_pass"] is False
    assert result["pass"] is False


def test_partial_history_cannot_be_reported_as_zero_load_or_complete():
    item = case()
    response = (
        "Tu n'as aucune charge cette semaine et ta Readiness est favorable. "
        "Maintiens ta séance tempo demain."
    )
    result = score_coaching_response(item, response)
    assert result["checks"]["action_pass"] is False
    assert result["checks"]["data_quality_pass"] is False
