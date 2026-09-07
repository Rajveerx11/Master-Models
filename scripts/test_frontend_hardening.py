"""Regression checks for dataset admission failures found during the V1 audit."""
import json
import unittest
from pathlib import Path

from scripts.audit_frontend_dataset import apply_edits, audit_trace, tool_contract_errors
from scripts.validate_v2_dataset import validate_final_approval, validate_split_isolation, validate_tools

TOOLS = json.loads((Path(__file__).resolve().parent.parent / "training/pi_tools.json").read_text())


def trace(calls):
    messages = [{"role": "user", "content": "Fix the component."}]
    for name, arguments, output in calls:
        messages += [{"role": "assistant", "tool_calls": [{"name": name, "arguments": arguments}]}, {"role": "tool", "name": name, "content": output}]
    messages.append({"role": "assistant", "content": "Changed the component."})
    return {"messages": messages}


def split_row(identifier, text="fix layout", commit="a" * 40):
    return {"id": identifier, "messages": [{"role": "user", "content": text}, {"role": "assistant", "content": identifier}], "source": {"repository": "example", "commit": commit}}


class TraceAuditTests(unittest.TestCase):
    def test_repeated_edit_target_cannot_claim_one_replacement(self):
        with self.assertRaisesRegex(ValueError, "2 times"):
            apply_edits("<Row />\n<Row />", [{"oldText": "<Row />", "newText": "<NewRow />"}])

    def test_edits_use_original_snapshot_and_reject_overlap(self):
        self.assertEqual(apply_edits("alpha beta", [{"oldText": "alpha", "newText": "beta"}, {"oldText": "beta", "newText": "gamma"}]), "beta gamma")
        with self.assertRaisesRegex(ValueError, "overlapping"):
            apply_edits("abcdef", [{"oldText": "abc", "newText": "x"}, {"oldText": "bc", "newText": "y"}])

    def test_argument_types_and_unknown_fields_are_rejected(self):
        for args in ({"path": 7}, {"path": "a.tsx", "invented": True}):
            row = trace([("read", args, "")])
            self.assertTrue(tool_contract_errors(row["messages"], TOOLS))

    def test_contiguous_multi_call_results_and_orphans(self):
        row = trace([("read", {"path": "a"}, "a")])
        row["messages"].insert(3, {"role": "tool", "name": "read", "content": "orphan"})
        self.assertTrue(tool_contract_errors(row["messages"], TOOLS))
        row = trace([("read", {"path": "a"}, "a")])
        row["messages"][1]["tool_calls"].append({"name": "read", "arguments": {"path": "b"}})
        self.assertTrue(tool_contract_errors(row["messages"], TOOLS))

    def test_code_error_field_is_not_failed_read(self):
        row = trace([("read", {"path": "a.ts"}, "interface S {\n  error: string\n}\n"), ("edit", {"path": "a.ts", "edits": [{"oldText": "error: string", "newText": "error: string | null"}]}, "ok"), ("bash", {"command": "npx tsc --noEmit"}, "")])
        findings, files, _, _ = audit_trace(row, TOOLS)
        self.assertIn("error: string | null", files["a.ts"])
        self.assertFalse(any(f["severity"] == "defect" for f in findings))
        self.assertIn("synthetic_execution_unverified", [f["code"] for f in findings])

    def test_empty_file_marker_and_tailwind_truncate_are_not_syntax(self):
        row = trace([("read", {"path": "empty.ts"}, "(file is empty - 0 bytes)"), ("read", {"path": "a.tsx"}, 'export const A = () => <p className="truncate">x</p>')])
        _, files, _, _ = audit_trace(row, TOOLS)
        self.assertEqual(files["empty.ts"], "")
        self.assertIn("a.tsx", files)

    def test_refused_and_partial_reads_do_not_become_full_source(self):
        row = trace([("read", {"path": "a.tsx"}, "read_file: file too large. No content returned."), ("read", {"path": "b.ts", "offset": 200, "limit": 10}, "const n = 1")])
        _, files, _, _ = audit_trace(row, TOOLS)
        self.assertEqual(files, {})

    def test_check_before_last_edit_does_not_qualify(self):
        row = trace([("read", {"path": "a.ts"}, "const x = 1"), ("bash", {"command": "npx tsc --noEmit"}, ""), ("edit", {"path": "a.ts", "edits": [{"oldText": "1", "newText": "2"}]}, "ok")])
        findings, _, _, _ = audit_trace(row, TOOLS)
        self.assertIn("verification_before_last_edit", [f["code"] for f in findings])

    def test_general_enum_null_schema_mismatch_is_rejected(self):
        tools = [{"function": {"name": "copy", "parameters": {"type": "object", "properties": {"path": {"type": "string", "enum": [None]}}, "required": ["path"]}}}]
        row = trace([("copy", {"path": "/project"}, "ok")])
        self.assertTrue(tool_contract_errors(row["messages"], tools))


class V2AdmissionTests(unittest.TestCase):
    def test_split_rejects_paraphrase_of_same_source_task(self):
        with self.assertRaisesRegex(SystemExit, "source task overlap"):
            validate_split_isolation([split_row("a", "repair menu")], [split_row("b", "fix dropdown")])

    def test_split_rejects_normalized_prompt_overlap(self):
        with self.assertRaisesRegex(SystemExit, "prompt overlap"):
            validate_split_isolation([split_row("a", "FIX layout!")], [split_row("b", "fix layout", "b" * 40)])

    def test_distinct_source_tasks_pass(self):
        validate_split_isolation([split_row("a", "fix menu")], [split_row("b", "fix dialog", "b" * 40)])

    def test_generated_rejected_and_low_score_cannot_enter_final(self):
        for state, score in (("generated", 9), ("rejected", 9), ("judge_passed", 7), ("judge_passed", True)):
            with self.assertRaises(SystemExit):
                validate_final_approval({"quality": {"review_state": state, "judge_score": score}}, "fixture")

    def test_bash_requires_real_integer_metadata(self):
        row = trace([("bash", {"command": "npx tsc --noEmit"}, "")])
        for metadata in ({}, {"exit_code": False}):
            row["messages"][2]["metadata"] = metadata
            with self.assertRaisesRegex(SystemExit, "integer exit_code"):
                validate_tools(row["messages"], {"bash"}, "fixture")

    def test_zero_exit_cannot_mask_explicit_failure(self):
        row = trace([("bash", {"command": "npx vitest run"}, "FAIL a.test.ts\nTests 1 failed")])
        row["messages"][2]["metadata"] = {"exit_code": 0}
        with self.assertRaisesRegex(SystemExit, "contradicts"):
            validate_tools(row["messages"], {"bash"}, "fixture")

    def test_old_success_invalidated_by_later_edit(self):
        row = trace([("bash", {"command": "npx tsc --noEmit"}, ""), ("edit", {"path": "a", "edits": [{"oldText": "x", "newText": "y"}]}, "ok")])
        row["messages"][2]["metadata"] = {"exit_code": 0}
        self.assertEqual(validate_tools(row["messages"], {"bash", "edit"}, "fixture"), {})

    def test_reading_failure_log_is_not_failed_verification(self):
        row = trace([("bash", {"command": "cat previous-test.log"}, "FAIL a.test.ts")])
        row["messages"][2]["metadata"] = {"exit_code": 0}
        self.assertEqual(validate_tools(row["messages"], {"bash"}, "fixture"), {"cat previous-test.log": 1})


if __name__ == "__main__":
    unittest.main()
