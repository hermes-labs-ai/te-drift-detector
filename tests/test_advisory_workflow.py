"""Run the actual advisory assertion shell with synthetic action outputs."""
import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("receipt_kind", ["empty", "missing", "valid", "invalid", "malformed", "no-summary"])
def test_advisory_receipt_contract(tmp_path, receipt_kind):
    workflow = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"
    script = workflow.read_text().split("      - name: Assert advisory map contract", 1)[1]
    script = script.split("        run: |\n", 1)[1]
    script = "\n".join(line[10:] for line in script.splitlines())
    receipt = tmp_path / "receipt.json"
    summary = tmp_path / "summary.md"
    payload = {
        "schema_version": "intent-verify.coverage-map.v1",
        "acceptance_authority": False,
        "items": [{"verdict": "covered"}] * 3,
        "verdict": "covered",
    }
    if receipt_kind == "invalid":
        payload["acceptance_authority"] = True
    if receipt_kind not in {"empty", "missing"}:
        receipt.write_text("{" if receipt_kind == "malformed" else json.dumps(payload))
    env = dict(os.environ, RECEIPT="" if receipt_kind == "empty" else str(receipt),
               SUMMARY_WRITTEN="false" if receipt_kind == "no-summary" else "true",
               GITHUB_STEP_SUMMARY=str(summary))
    result = subprocess.run(["bash", "-e", "-c", script], env=env, capture_output=True, text=True)
    if receipt_kind in {"empty", "missing"}:
        assert result.returncode == 0
        assert "::warning::" in result.stdout
        assert "no receipt was produced" in summary.read_text()
    elif receipt_kind == "valid":
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode != 0
