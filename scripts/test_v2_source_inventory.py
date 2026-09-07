"""Regression coverage for frozen-eval source exclusion."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_v2_source_inventory as inventory


class EvalReservationTests(unittest.TestCase):
    def test_legacy_and_v2_reference_formats_are_reserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "legacy.md").write_text("Source: `C:/repo` commit `abcdef1`", encoding="utf-8")
            reference = "2" * 40
            (root / "v2.md").write_text(
                f"Reference commit: `{reference}`\nStart commit: `{'3' * 40}`",
                encoding="utf-8",
            )
            with patch.object(inventory, "EVAL_ROOT", root):
                self.assertEqual(inventory.eval_short_hashes(), {"abcdef1", reference})

    def test_candidates_cannot_use_reserved_reference_or_parent(self):
        specialist = {
            "id": "frontend-stack", "sources": ["repo"], "subject_keywords": ["fix"],
            "path_patterns": [], "eval_state": "frozen", "generation_gate": "open",
        }
        records = [
            {"commit": commit, "parent": parent, "subject": "fix UI", "changed_files": ["src/a.tsx"]}
            for commit, parent in [("reserved", "a"), ("b", "reserved"), ("c", "d")]
        ]
        with patch.object(inventory, "run_git", return_value="head"):
            data, _ = inventory.build_for_specialist(
                specialist, {"repo": {"path": "."}}, {"repo": records}, {"reserved"}
            )
        import json
        self.assertEqual([json.loads(line)["commit"] for line in data.splitlines()], ["c"])


if __name__ == "__main__":
    unittest.main()
