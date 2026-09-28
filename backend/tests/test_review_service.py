import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.review import ReviewPayload
from app.services import review_service
from app.services.diff_parser import parse_unified_diff, validate_finding_location


def test_review_evaluation_fixtures_have_grounded_expected_locations():
    fixture_path = Path(__file__).parent / "fixtures" / "review_eval" / "cases.json"
    cases = json.loads(fixture_path.read_text())
    assert len(cases) >= 2
    for case in cases:
        parsed = parse_unified_diff(case["diff"])
        for expected in case["expected_findings"]:
            assert validate_finding_location(
                expected["file"],
                expected["line_start"],
                expected["line_end"],
                parsed,
            )


@pytest.mark.asyncio
async def test_review_service_filters_ungrounded_findings(monkeypatch):
    async def fake_generate(self, prompt, *, temperature=0.1, json_mode=False):
        return (
            '{"summary":"Adds a guarded operation.","findings":['
            '{"severity":"major","category":"security","file":"src/a.py",'
            '"line_start":2,"line_end":2,"title":"Risk","explanation":"A risk.","suggested_fix":"Guard it."},'
            '{"severity":"critical","category":"bug","file":"imagined.py",'
            '"line_start":2,"line_end":2,"title":"Made up","explanation":"Unsupported.","suggested_fix":""}]}'
        )

    monkeypatch.setattr(review_service.GoogleAIClient, "generate", fake_generate)
    diff = "diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1 +1,2 @@\n keep()\n+guarded()\n"
    summary, findings, files, excluded, count = await review_service.review_diff(diff)
    assert summary == "Adds a guarded operation."
    assert len(findings) == 1
    assert findings[0].file == "src/a.py"
    assert [file.path for file in files] == ["src/a.py"]
    assert excluded == []
    assert count == 1


def test_review_payload_rejects_invalid_severity_and_reversed_range():
    with pytest.raises(ValidationError):
        ReviewPayload.model_validate(
            {
                "summary": "x",
                "findings": [
                    {
                        "severity": "urgent",
                        "category": "bug",
                        "file": "a.py",
                        "line_start": 3,
                        "line_end": 2,
                        "title": "x",
                        "explanation": "y",
                        "suggested_fix": "z",
                    }
                ],
            }
        )


@pytest.mark.asyncio
async def test_review_output_gets_one_repair_attempt(monkeypatch):
    responses = iter(["not json", '{"summary":"fixed","findings":[]}'])

    async def fake_generate(self, prompt, *, temperature=0.1, json_mode=False):
        return next(responses)

    monkeypatch.setattr(review_service.GoogleAIClient, "generate", fake_generate)
    payload = await review_service._validated_payload(review_service.GoogleAIClient(), "prompt")
    assert payload.summary == "fixed"
    with pytest.raises(StopIteration):
        next(responses)
