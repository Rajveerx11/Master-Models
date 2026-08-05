import json
import unittest

from scripts.gate_proxy import (
    EMPTY_SENTINEL,
    guard_response,
    normalize_empty_tool_results,
    repair_xml_calls,
    sse_bytes,
)
from scripts.verify_server_template import normalize_json_blocks


class GateProxyTests(unittest.TestCase):
    def test_empty_tool_result_gets_sentinel(self):
        body = {"messages": [{"role": "tool", "content": ""}, {"role": "tool", "content": "ok"}]}
        self.assertEqual(normalize_empty_tool_results(body), 1)
        self.assertEqual(body["messages"][0]["content"], EMPTY_SENTINEL)

    def test_repairs_function_xml(self):
        calls, residual = repair_xml_calls(
            "before <function=read><parameter=path>src/a.ts</parameter></function> after"
        )
        self.assertEqual(calls[0]["function"]["name"], "read")
        self.assertEqual(json.loads(calls[0]["function"]["arguments"]), {"path": "src/a.ts"})
        self.assertEqual(residual, "before  after")

    def test_repairs_qwen_tool_call_xml(self):
        calls, residual = repair_xml_calls(
            '<tool_call>\n{"name":"grep","arguments":{"pattern":"TODO"}}\n</tool_call>'
        )
        self.assertEqual(calls[0]["function"]["name"], "grep")
        self.assertEqual(residual, "")

    def test_guard_sets_tool_finish_reason(self):
        response = {
            "choices": [{
                "message": {"role": "assistant", "content": "<function=ls></function>"},
                "finish_reason": "stop",
            }]
        }
        guarded, label = guard_response(response)
        self.assertEqual(label, "repaired")
        self.assertEqual(guarded["choices"][0]["finish_reason"], "tool_calls")

    def test_sse_contains_tool_delta_and_done(self):
        response = {
            "id": "x",
            "model": "local",
            "choices": [{
                "message": {"role": "assistant", "content": None, "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "read", "arguments": '{"path":"a.ts"}'},
                }]},
                "finish_reason": "tool_calls",
            }],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        }
        text = sse_bytes(response).decode("utf-8")
        self.assertIn('"tool_calls"', text)
        self.assertTrue(text.endswith("data: [DONE]\n\n"))

    def test_template_normalizer_changes_only_json_whitespace(self):
        spaced = '<tools>\n{"description": "keep comma, space", "n": 1}\n</tools>'
        compact = '<tools>\n{"description":"keep comma, space","n":1}\n</tools>'
        self.assertEqual(normalize_json_blocks(spaced), normalize_json_blocks(compact))


if __name__ == "__main__":
    unittest.main()
