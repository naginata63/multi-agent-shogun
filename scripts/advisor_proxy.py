#!/usr/bin/env python3
"""Advisor Proxy for GLM Agents — Port 8780

GLM (Z.AI) does not implement the Anthropic Advisor Tool server-side.
This proxy intercepts advisor tool_use calls, gets advice via claude -p,
injects the tool_result, and continues the conversation with Z.AI.

Architecture:
  Claude Code → localhost:8780 → api.z.ai/api/anthropic
                     ↓ advisor tool_use detected
               claude -p (subscription, no extra cost)
                     ↓
               tool_result → Z.AI → continuation → Claude Code
"""

import asyncio
import copy
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from logging.handlers import RotatingFileHandler

from aiohttp import web, ClientSession, ClientTimeout

# ─── Constants ────────────────────────────────────────────────────────────────

PROXY_PORT = 8780
UPSTREAM_URL = "https://api.z.ai/api/anthropic"
CLAUDE_CLI = os.path.expanduser("~/.local/bin/claude")
ADVISOR_MODEL = os.environ.get("ADVISOR_MODEL", "claude-sonnet-4-6")  # cmd_1477: Opus 1M→Sonnet 4.6 (CLI起動+1M読込で120sタイムアウト恒常化の根本対処)
ADVISOR_TIMEOUT = 120  # seconds for claude -p
UPSTREAM_TIMEOUT = 300  # seconds for Z.AI responses
MAX_ADVISOR_LOOPS = 3
ADVISOR_TOOL_DEF = {
    "name": "advisor",
    "description": "Consult a stronger reviewer who sees your full conversation transcript. No parameters. Call before substantive work and when stuck.",
    "input_schema": {"type": "object", "properties": {}},
}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
PID_FILE = os.path.join(LOG_DIR, "advisor_proxy.pid")
ADVISOR_CALLS_LOG = os.path.join(LOG_DIR, "advisor_calls.log")  # cmd_1442 H10改 done_gate.sh 参照用

_START_TIME = time.time()

# ─── Circuit Breaker ──────────────────────────────────────────────────────────


class CircuitBreaker:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._lock = threading.Lock()

    def record_success(self):
        with self._lock:
            self.failure_count = 0
            self.state = self.CLOSED

    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = self.OPEN
                logger.warning("Circuit OPEN — %d consecutive failures", self.failure_count)

    def can_request(self) -> bool:
        with self._lock:
            if self.state == self.CLOSED:
                return True
            if self.state == self.OPEN:
                if self.last_failure_time and (time.time() - self.last_failure_time) >= self.recovery_timeout:
                    self.state = self.HALF_OPEN
                    logger.info("Circuit → HALF_OPEN (recovery timeout elapsed)")
                    return True
                return False
            # HALF_OPEN — allow one probe request
            return True


circuit_breaker = CircuitBreaker()

# ─── Metrics ──────────────────────────────────────────────────────────────────


class Metrics:
    def __init__(self, max_response_samples=100):
        self._lock = threading.Lock()
        self.total_requests = 0
        self.success = 0
        self.failures = 0
        self.advisor_calls = 0
        self._response_times = []
        self._max_samples = max_response_samples

    def record_request(self):
        with self._lock:
            self.total_requests += 1

    def record_success(self, elapsed_ms: float):
        with self._lock:
            self.success += 1
            self._response_times.append(elapsed_ms)
            if len(self._response_times) > self._max_samples:
                self._response_times = self._response_times[-self._max_samples:]

    def record_failure(self):
        with self._lock:
            self.failures += 1

    def record_advisor_call(self):
        with self._lock:
            self.advisor_calls += 1

    def avg_response_ms(self) -> float:
        with self._lock:
            if not self._response_times:
                return 0.0
            return sum(self._response_times) / len(self._response_times)


metrics = Metrics()

# ─── Logging ──────────────────────────────────────────────────────────────────

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("advisor_proxy")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "advisor_proxy.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(handler)

# Also log to stderr for startup visibility
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(stderr_handler)

# ─── Advisor Detection ────────────────────────────────────────────────────────


def detect_advisor_tool_use(response_body: dict) -> dict | None:
    """Find advisor tool_use in response content blocks."""
    for block in response_body.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == "advisor":
            return block
    return None


def log_advisor_call(agent_id: str | None, task_id: str | None, req_id: str) -> None:
    """Append advisor call event to logs/advisor_calls.log (cmd_1442 H10改).

    Format: ISO8601\tagent_id\ttask_id\tsource=advisor_proxy\treq_id=<req_id>
    done_gate.sh greps this log to verify 2x advisor call requirement.
    Best-effort; never raises.
    """
    try:
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
        agent = agent_id or "unknown"
        task = task_id or "unknown"
        line = f"{ts}\t{agent}\t{task}\tsource=advisor_proxy\treq_id={req_id}\n"
        with open(ADVISOR_CALLS_LOG, "a") as f:
            f.write(line)
    except Exception as e:
        logger.warning("advisor_calls.log write failed: %s", e)


# ─── Context Extraction ──────────────────────────────────────────────────────


def extract_context_for_advisor(request_body: dict) -> str:
    """Build a concise context string from conversation for claude -p."""
    parts = []

    # System prompt (truncated)
    system = request_body.get("system", "")
    if isinstance(system, str) and system:
        parts.append(f"[System prompt excerpt]: {system[:800]}")
    elif isinstance(system, list):
        text = " ".join(b.get("text", "") for b in system if b.get("type") == "text")
        if text:
            parts.append(f"[System prompt excerpt]: {text[:800]}")

    # Recent messages (last 6 to keep context manageable)
    messages = request_body.get("messages", [])
    recent = messages[-6:] if len(messages) > 6 else messages
    for msg in recent:
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if isinstance(content, str):
            text = content[:1500]
        elif isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", "")[:500])
                    elif block.get("type") == "tool_use":
                        text_parts.append(f"[tool_use: {block.get('name', '?')}]")
                    elif block.get("type") == "tool_result":
                        result_text = block.get("content", "")
                        if isinstance(result_text, str):
                            text_parts.append(f"[tool_result: {result_text[:300]}]")
                        elif isinstance(result_text, list):
                            for rb in result_text:
                                if rb.get("type") == "text":
                                    text_parts.append(f"[tool_result: {rb.get('text', '')[:300]}]")
            text = "\n".join(text_parts)[:1500]
        else:
            text = str(content)[:500]
        parts.append(f"{role}: {text}")

    return "\n\n".join(parts)


# ─── Claude -p Advisor Call ───────────────────────────────────────────────────


async def call_advisor_cli(context: str, model_override: str | None = None) -> str:
    """Call claude -p to get advisor response. Runs in thread pool.

    Args:
        context: conversation context to send to advisor
        model_override: optional per-request model ID (from X-Advisor-Model header).
                        Falls back to ADVISOR_MODEL env default if None.
    """
    prompt = (
        "You are an advisor reviewing an agent's work. "
        "Based on the conversation below, provide concise advice "
        "in under 100 words using enumerated steps.\n\n"
        f"{context}"
    )
    effective_model = model_override or ADVISOR_MODEL
    logger.info("call_advisor_cli: invoking claude -p with --model %s (override=%s)",
                effective_model, model_override or "none")

    def _run():
        try:
            result = subprocess.run(
                [CLAUDE_CLI, "-p", prompt, "--output-format", "text",
                 "--model", effective_model],
                capture_output=True,
                text=True,
                timeout=ADVISOR_TIMEOUT,
                env={**os.environ, "HOME": os.path.expanduser("~")},
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            logger.warning("claude -p returned code %d: %s", result.returncode, result.stderr[:200])
            return "Advisor unavailable. Proceed with your best judgment."
        except subprocess.TimeoutExpired:
            logger.warning("claude -p timed out after %ds", ADVISOR_TIMEOUT)
            return "Advisor unavailable (timeout). Proceed with your best judgment."
        except FileNotFoundError:
            logger.error("claude CLI not found at %s", CLAUDE_CLI)
            return "Advisor unavailable (CLI not found). Proceed with your best judgment."

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run)


# ─── Continuation Request Builder ────────────────────────────────────────────


def build_continuation(
    original_body: dict,
    response_body: dict,
    advisor_block: dict,
    advice: str,
) -> dict:
    """Build a new request with tool_result appended to messages."""
    body = copy.deepcopy(original_body)
    body["stream"] = False

    # Append assistant response
    body["messages"].append({
        "role": "assistant",
        "content": response_body["content"],
    })

    # Append tool_result
    body["messages"].append({
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": advisor_block["id"],
                "content": advice,
            }
        ],
    })

    return body


# ─── SSE Synthesis ────────────────────────────────────────────────────────────


def synthesize_sse(response_json: dict) -> list[bytes]:
    """Convert a non-streaming JSON response to SSE events."""
    events = []

    def sse(event_type: str, data: dict) -> bytes:
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode()

    # message_start
    msg_start = {k: v for k, v in response_json.items() if k != "content"}
    msg_start["content"] = []
    events.append(sse("message_start", {"type": "message_start", "message": msg_start}))

    # ping
    events.append(sse("ping", {"type": "ping"}))

    # Content blocks
    for idx, block in enumerate(response_json.get("content", [])):
        block_type = block.get("type", "text")

        if block_type == "text":
            # content_block_start
            events.append(sse("content_block_start", {
                "type": "content_block_start",
                "index": idx,
                "content_block": {"type": "text", "text": ""},
            }))
            # content_block_delta — send text in one chunk
            text = block.get("text", "")
            if text:
                events.append(sse("content_block_delta", {
                    "type": "content_block_delta",
                    "index": idx,
                    "delta": {"type": "text_delta", "text": text},
                }))
            # content_block_stop
            events.append(sse("content_block_stop", {
                "type": "content_block_stop",
                "index": idx,
            }))

        elif block_type == "tool_use":
            # For non-advisor tool_use, pass through
            events.append(sse("content_block_start", {
                "type": "content_block_start",
                "index": idx,
                "content_block": {"type": "tool_use", "id": block.get("id", ""), "name": block.get("name", ""), "input": {}},
            }))
            input_json = json.dumps(block.get("input", {}))
            events.append(sse("content_block_delta", {
                "type": "content_block_delta",
                "index": idx,
                "delta": {"type": "input_json_delta", "partial_json": input_json},
            }))
            events.append(sse("content_block_stop", {
                "type": "content_block_stop",
                "index": idx,
            }))

        elif block_type == "thinking":
            events.append(sse("content_block_start", {
                "type": "content_block_start",
                "index": idx,
                "content_block": {"type": "thinking", "thinking": ""},
            }))
            thinking_text = block.get("thinking", "")
            if thinking_text:
                events.append(sse("content_block_delta", {
                    "type": "content_block_delta",
                    "index": idx,
                    "delta": {"type": "thinking_delta", "thinking": thinking_text},
                }))
            events.append(sse("content_block_stop", {
                "type": "content_block_stop",
                "index": idx,
            }))

    # message_delta
    events.append(sse("message_delta", {
        "type": "message_delta",
        "delta": {"stop_reason": response_json.get("stop_reason", "end_turn")},
        "usage": response_json.get("usage", {}),
    }))

    # message_stop
    events.append(sse("message_stop", {"type": "message_stop"}))

    return events


# ─── Request Handler ──────────────────────────────────────────────────────────

RETRY_MAX = 2
RETRY_BACKOFFS = [1, 2]  # seconds


async def _upstream_post(
    session: ClientSession, url: str, json_body: dict, headers: dict
) -> tuple[int, dict | bytes | None, str | None]:
    """Post to upstream. Returns (status, response_json_or_body, error_msg)."""
    try:
        async with session.post(url, json=json_body, headers=headers) as resp:
            if resp.status != 200:
                resp_body = await resp.read()
                return resp.status, resp_body, None
            response_json = await resp.json()
            return 200, response_json, None
    except Exception as e:
        return 502, None, str(e)


async def handle_request(request: web.Request) -> web.StreamResponse:
    """Handle all incoming requests — proxy to Z.AI with advisor interception.

    Clients may specify `X-Advisor-Model: claude-opus-4-6[1m]` to override the
    default advisor model per-request (no proxy restart required).
    """
    req_id = uuid.uuid4().hex[:8]
    path = request.path
    body = await request.read()
    start_time = time.time()

    # Per-request advisor model override (fallback to ADVISOR_MODEL env default)
    advisor_model_override = request.headers.get("X-Advisor-Model")
    if advisor_model_override:
        logger.info("[%s] X-Advisor-Model override: %s", req_id, advisor_model_override)

    # Circuit breaker check
    if not circuit_breaker.can_request():
        logger.warning("[%s] Rejected — circuit OPEN", req_id)
        return web.Response(status=503, text="Service unavailable (circuit breaker open)")

    metrics.record_request()

    # Forward headers (exclude hop-by-hop)
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length", "transfer-encoding")
    }

    upstream_url = UPSTREAM_URL + path
    method = request.method

    # Only intercept POST /v1/messages
    if method != "POST" or path != "/v1/messages":
        logger.info("[%s] Passthrough %s %s", req_id, method, path)
        timeout = ClientTimeout(total=UPSTREAM_TIMEOUT)
        async with ClientSession(timeout=timeout) as session:
            async with session.request(method, upstream_url, headers=headers, data=body) as resp:
                resp_body = await resp.read()
                return web.Response(
                    status=resp.status,
                    headers={k: v for k, v in resp.headers.items()
                             if k.lower() not in ("content-encoding", "transfer-encoding", "content-length")},
                    body=resp_body,
                )

    # Parse request body
    try:
        request_json = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return web.Response(status=400, text="Invalid JSON")

    wants_stream = request_json.get("stream", False)

    # Inject advisor tool definition so GLM agents can call advisor()
    tools = request_json.setdefault("tools", [])
    if not any(t.get("name") == "advisor" for t in tools):
        tools.append(ADVISOR_TOOL_DEF)
        logger.info("Injected advisor tool definition into request")

    # Inject advisor mandatory reminder into system prompt
    ADVISOR_REMINDER = (
        "\n\n[MANDATORY] You MUST call advisor() exactly twice per task: "
        "once BEFORE starting implementation (step 3.8) and once AFTER completing implementation (step 4.8). "
        "This is required regardless of task difficulty or size. Skipping advisor() because the task seems simple is FORBIDDEN."
    )
    system = request_json.get("system", "")
    if isinstance(system, str):
        if "MUST call advisor()" not in system:
            request_json["system"] = system + ADVISOR_REMINDER
    elif isinstance(system, list):
        texts = [b.get("text", "") for b in system if b.get("type") == "text"]
        if not any("MUST call advisor()" in t for t in texts):
            system.append({"type": "text", "text": ADVISOR_REMINDER})

    # Send non-streaming to Z.AI (with retry)
    upstream_body = copy.deepcopy(request_json)
    upstream_body["stream"] = False

    logger.info("[%s] Messages request — model=%s stream=%s", req_id, request_json.get("model"), wants_stream)

    timeout = ClientTimeout(total=UPSTREAM_TIMEOUT)
    response_json = None
    last_status = 0
    last_error = None

    async with ClientSession(timeout=timeout) as session:
        for attempt in range(RETRY_MAX + 1):
            status, resp_data, error = await _upstream_post(
                session, upstream_url, upstream_body, headers
            )
            last_status = status

            if status == 200:
                response_json = resp_data
                break

            # Retry only on 5xx or connection errors (502)
            if status >= 500 and attempt < RETRY_MAX:
                backoff = RETRY_BACKOFFS[attempt]
                logger.warning("[%s] Upstream %d, retrying in %ds (attempt %d/%d)",
                               req_id, status, backoff, attempt + 1, RETRY_MAX)
                await asyncio.sleep(backoff)
                continue

            # Non-retryable or exhausted retries
            if error is None and isinstance(resp_data, bytes):
                return web.Response(status=status, body=resp_data, content_type="application/json")
            elif error:
                last_error = error
                break
            break

    if response_json is None:
        elapsed_ms = (time.time() - start_time) * 1000
        metrics.record_failure()
        circuit_breaker.record_failure()
        logger.error("[%s] All retries exhausted — last_status=%d", req_id, last_status)
        return web.Response(status=last_status or 502, text=f"Upstream error: {last_error or 'exhausted retries'}")

    # Success — record metrics
    elapsed_ms = (time.time() - start_time) * 1000
    metrics.record_success(elapsed_ms)
    circuit_breaker.record_success()

    # Advisor interception loop
    current_request = request_json
    for i in range(MAX_ADVISOR_LOOPS):
        advisor_block = detect_advisor_tool_use(response_json)
        if not advisor_block:
            break

        metrics.record_advisor_call()
        logger.info("[%s] Advisor tool_use detected (loop %d/%d), id=%s",
                     req_id, i + 1, MAX_ADVISOR_LOOPS, advisor_block.get("id"))

        # cmd_1442 H10改: advisor 呼出を logs/advisor_calls.log に記録
        # agent_id / task_id はクライアント側ヘッダ (X-Agent-Id / X-Current-Task) 優先、
        # なければ system prompt からの推測 (失敗時 unknown)
        hdr_agent = request.headers.get("X-Agent-Id")
        hdr_task = request.headers.get("X-Current-Task")
        log_advisor_call(hdr_agent, hdr_task, req_id)

        # Get advice via claude -p (per-request model override via X-Advisor-Model header)
        context = extract_context_for_advisor(current_request)
        logger.info("[%s] Advisor context (%d chars): %s", req_id, len(context), context[:300])
        advice = await call_advisor_cli(context, model_override=advisor_model_override)
        logger.info("[%s] Advisor response (%d chars): %s", req_id, len(advice), advice[:200])

        # Build continuation request
        current_request = build_continuation(current_request, response_json, advisor_block, advice)

        # Send continuation to Z.AI (no retry for advisor continuations)
        try:
            async with ClientSession(timeout=timeout) as session:
                async with session.post(upstream_url, json=current_request, headers=headers) as resp:
                    if resp.status != 200:
                        resp_body = await resp.read()
                        metrics.record_failure()
                        circuit_breaker.record_failure()
                        logger.warning("Continuation upstream error %d", resp.status)
                        return web.Response(status=resp.status, body=resp_body,
                                            content_type=resp.content_type)
                    response_json = await resp.json()
        except Exception as e:
            metrics.record_failure()
            circuit_breaker.record_failure()
            logger.error("Continuation request failed: %s", e)
            return web.Response(status=502, text=f"Upstream error: {e}")

    # Return response to Claude Code
    if wants_stream:
        resp = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await resp.prepare(request)
        for chunk in synthesize_sse(response_json):
            await resp.write(chunk)
        await resp.write_eof()
        return resp
    else:
        return web.json_response(response_json)


# ─── Health Check ─────────────────────────────────────────────────────────────


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
        "port": PROXY_PORT,
        "upstream": UPSTREAM_URL,
        "uptime_seconds": int(time.time() - _START_TIME),
        "circuit_state": circuit_breaker.state,
    })


# ─── Metrics Endpoint ─────────────────────────────────────────────────────────


async def handle_metrics(request: web.Request) -> web.Response:
    return web.json_response({
        "total_requests": metrics.total_requests,
        "success": metrics.success,
        "failures": metrics.failures,
        "advisor_calls": metrics.advisor_calls,
        "avg_response_ms": metrics.avg_response_ms(),
        "circuit_state": circuit_breaker.state,
    })


# ─── Main ─────────────────────────────────────────────────────────────────────


def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_pid():
    try:
        os.remove(PID_FILE)
    except OSError:
        pass


async def on_shutdown(app):
    remove_pid()


def main():
    write_pid()

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/metrics", handle_metrics)
    app.router.add_route("*", "/{path:.*}", handle_request)

    logger.info("Advisor Proxy starting on port %d → %s", PROXY_PORT, UPSTREAM_URL)
    logger.info("Claude CLI: %s", CLAUDE_CLI)
    logger.info("PID: %d", os.getpid())

    # Graceful shutdown on signals
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: sys.exit(0))

    web.run_app(app, host="127.0.0.1", port=PROXY_PORT, print=None)


if __name__ == "__main__":
    main()
