"""OpenAI-compatible guard proxy for the frozen three-arm gate.

Pi/Neura connects to port 8080. llama-server runs on port 8081. The proxy keeps
both documented harness guards identical across every arm:

1. Empty tool results become an explicit empty-file sentinel.
2. Raw Qwen XML tool calls are repaired; unparseable XML gets one retry.

Streaming requests are evaluated upstream as one non-streaming response, guarded,
then emitted as a valid OpenAI SSE stream for pi.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

EMPTY_SENTINEL = "(file is empty - 0 bytes)"
RETRY_PROMPT = (
    "Your tool call was malformed and could not be parsed. "
    "Re-emit it as one or more valid tool calls using the provided tool schemas."
)
FUNCTION_RE = re.compile(r"<function=(\w+)>(.*?)</function>", re.S)
PARAM_RE = re.compile(r"<parameter=(\w+)>\n?(.*?)</parameter>", re.S)
TOOL_CALL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.S)


def normalize_empty_tool_results(body: dict) -> int:
    count = 0
    for message in body.get("messages") or []:
        if message.get("role") == "tool" and message.get("content") == "":
            message["content"] = EMPTY_SENTINEL
            count += 1
    return count


def _tool_call(name: str, arguments: dict) -> dict:
    return {
        "id": f"call_{uuid.uuid4().hex[:16]}",
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False)},
    }


def repair_xml_calls(text: str) -> tuple[list[dict], str]:
    calls: list[dict] = []
    spans: list[tuple[int, int]] = []

    for match in FUNCTION_RE.finditer(text):
        args = {name: value.strip("\n") for name, value in PARAM_RE.findall(match.group(2))}
        calls.append(_tool_call(match.group(1), args))
        spans.append(match.span())

    for match in TOOL_CALL_RE.finditer(text):
        try:
            raw = json.loads(match.group(1))
            fn = raw.get("function", raw)
            name = fn["name"]
            args = fn.get("arguments", {})
            if isinstance(args, str):
                args = json.loads(args)
            if not isinstance(args, dict):
                continue
        except (KeyError, TypeError, json.JSONDecodeError):
            continue
        calls.append(_tool_call(name, args))
        spans.append(match.span())

    residual = text
    for start, end in sorted(spans, reverse=True):
        residual = residual[:start] + residual[end:]
    return calls, residual.strip()


def guard_response(response: dict) -> tuple[dict, str | None]:
    choices = response.get("choices") or []
    if not choices:
        return response, None
    choice = choices[0]
    message = choice.get("message") or {}
    if message.get("tool_calls"):
        return response, None
    content = message.get("content") or ""
    calls, residual = repair_xml_calls(content)
    if not calls:
        return response, None
    message["tool_calls"] = calls
    message["content"] = residual or None
    choice["finish_reason"] = "tool_calls"
    return response, "repaired"


def sse_bytes(response: dict) -> bytes:
    choice = (response.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    response_id = response.get("id") or f"chatcmpl-{uuid.uuid4().hex}"
    created = response.get("created") or int(time.time())
    model = response.get("model") or "local"

    def chunk(delta: dict, finish_reason=None) -> bytes:
        payload = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
        }
        return b"data: " + json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n\n"

    out = bytearray(chunk({"role": "assistant"}))
    if message.get("content"):
        out.extend(chunk({"content": message["content"]}))
    if message.get("tool_calls"):
        tool_deltas = []
        for index, call in enumerate(message["tool_calls"]):
            fn = call.get("function", call)
            arguments = fn.get("arguments", "{}")
            if not isinstance(arguments, str):
                arguments = json.dumps(arguments, ensure_ascii=False)
            tool_deltas.append({
                "index": index,
                "id": call.get("id") or f"call_{uuid.uuid4().hex[:16]}",
                "type": "function",
                "function": {"name": fn.get("name"), "arguments": arguments},
            })
        out.extend(chunk({"tool_calls": tool_deltas}))
    out.extend(chunk({}, choice.get("finish_reason") or "stop"))
    if response.get("usage") is not None:
        usage = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [],
            "usage": response["usage"],
        }
        out.extend(b"data: " + json.dumps(usage).encode("utf-8") + b"\n\n")
    out.extend(b"data: [DONE]\n\n")
    return bytes(out)


class GuardProxy:
    def __init__(self, upstream: str, log_path: Path):
        self.upstream = upstream.rstrip("/")
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()

    def upstream_call(self, path: str, body: dict, timeout: int = 1800) -> dict:
        request = urllib.request.Request(
            self.upstream + path,
            json.dumps(body).encode("utf-8"),
            {"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)

    def log(self, record: dict) -> None:
        record = {"at": datetime.now(timezone.utc).isoformat(), **record}
        with self.lock, self.log_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def handler_factory(proxy: GuardProxy):
    class Handler(BaseHTTPRequestHandler):
        server_version = "MasterModelsGateProxy/1.0"

        def log_message(self, _format, *_args):
            return

        def _send(self, status: int, content_type: str, data: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            try:
                with urllib.request.urlopen(proxy.upstream + self.path, timeout=30) as response:
                    self._send(response.status, response.headers.get_content_type(), response.read())
            except urllib.error.HTTPError as error:
                self._send(error.code, "application/json", error.read())
            except Exception as error:
                self._send(502, "application/json", json.dumps({"error": str(error)}).encode())

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            if self.path != "/v1/chat/completions":
                try:
                    request = urllib.request.Request(
                        proxy.upstream + self.path,
                        raw,
                        {"Content-Type": self.headers.get("Content-Type", "application/json")},
                    )
                    with urllib.request.urlopen(request, timeout=1800) as response:
                        self._send(response.status, response.headers.get_content_type(), response.read())
                except urllib.error.HTTPError as error:
                    self._send(error.code, "application/json", error.read())
                except Exception as error:
                    self._send(502, "application/json", json.dumps({"error": str(error)}).encode())
                return

            started = time.time()
            try:
                body = json.loads(raw)
                wanted_stream = bool(body.get("stream"))
                body["stream"] = False
                # OpenAI defines stream_options only for streaming requests. The
                # proxy buffers upstream so it can validate/repair tool calls, then
                # recreates SSE for the client.
                body.pop("stream_options", None)
                empty_count = normalize_empty_tool_results(body)
                response = proxy.upstream_call(self.path, body)
                response, guard = guard_response(response)

                choice = (response.get("choices") or [{}])[0]
                message = choice.get("message") or {}
                content = message.get("content") or ""
                raw_xml = "<function=" in content or "<tool_call>" in content
                if raw_xml and not message.get("tool_calls"):
                    retry_body = dict(body)
                    retry_body["messages"] = list(body.get("messages") or []) + [
                        {"role": "assistant", "content": content},
                        {"role": "user", "content": RETRY_PROMPT},
                    ]
                    response = proxy.upstream_call(self.path, retry_body)
                    response, retry_guard = guard_response(response)
                    guard = "retried+repaired" if retry_guard else "retried"

                final_choice = (response.get("choices") or [{}])[0]
                final_message = final_choice.get("message") or {}
                proxy.log({
                    "path": self.path,
                    "latency_s": round(time.time() - started, 3),
                    "empty_tool_results_normalized": empty_count,
                    "guard": guard,
                    "tool_calls": len(final_message.get("tool_calls") or []),
                    "finish_reason": final_choice.get("finish_reason"),
                })
                if wanted_stream:
                    self._send(200, "text/event-stream; charset=utf-8", sse_bytes(response))
                else:
                    self._send(200, "application/json", json.dumps(response).encode("utf-8"))
            except urllib.error.HTTPError as error:
                self._send(error.code, "application/json", error.read())
            except Exception as error:
                proxy.log({"path": self.path, "error": str(error)})
                self._send(502, "application/json", json.dumps({"error": str(error)}).encode())

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--upstream", default="http://127.0.0.1:8081")
    ap.add_argument("--log", type=Path, required=True)
    args = ap.parse_args()
    proxy = GuardProxy(args.upstream, args.log)
    server = ThreadingHTTPServer((args.host, args.port), handler_factory(proxy))
    print(f"gate proxy http://{args.host}:{args.port} -> {args.upstream}")
    server.serve_forever()


if __name__ == "__main__":
    main()
