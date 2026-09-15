from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

SEARCH_COMMAND = re.compile(r"(?:^|[\s;|&(])(grep|rg|findstr|find|ls|dir|tree|Select-String|Get-ChildItem)(?=\s|$)")


def _ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_session(path: Path) -> dict:
    tools = Counter()
    stop_reasons = Counter()
    usage = Counter()
    cost = 0.0
    assistant_messages = tool_errors = transport_failures = compactions = 0
    bash_commands: list[str] = []
    read_paths: list[str] = []
    timestamps: list[datetime] = []
    model = thinking = error_message = None
    final_text = ""

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if isinstance(entry.get("timestamp"), str) and (ts := _ts(entry["timestamp"])):
            timestamps.append(ts)
        kind = entry.get("type")
        if kind == "model_change":
            model = f"{entry.get('provider')}/{entry.get('modelId')}"
        elif kind == "thinking_level_change":
            thinking = entry.get("thinkingLevel")
        elif kind == "compaction":
            compactions += 1
        elif kind == "message":
            message = entry["message"]
            role = message.get("role")
            if role == "assistant":
                assistant_messages += 1
                u = message.get("usage") or {}
                for key in ("input", "output", "cacheRead", "cacheWrite", "reasoning", "totalTokens"):
                    usage[key] += u.get(key) or 0
                cost += (u.get("cost") or {}).get("total") or 0.0
                stop_reasons[message.get("stopReason")] += 1
                if message.get("errorMessage"):
                    error_message = message["errorMessage"]
                transport_failures += sum(
                    1 for d in message.get("diagnostics") or [] if d.get("type") == "provider_transport_failure"
                )
                for block in message.get("content") or []:
                    if block.get("type") == "toolCall":
                        name = block.get("name")
                        tools[name] += 1
                        args = block.get("arguments") or {}
                        if name in ("bash", "powershell"):
                            bash_commands.append(str(args.get("command", "")))
                        elif name == "read":
                            read_paths.append(str(args.get("path", "")))
                    elif block.get("type") == "text" and block.get("text"):
                        final_text = block["text"]
            elif role == "toolResult" and message.get("isError"):
                tool_errors += 1
            elif role == "compactionSummary":
                compactions += 1

    search_hits = Counter(m.group(1) for c in bash_commands for m in SEARCH_COMMAND.finditer(c))
    normalized_reads = [p.replace("\\", "/") for p in read_paths]
    return {
        "model": model,
        "thinking_level": thinking,
        "assistant_messages": assistant_messages,
        "tool_calls": sum(tools.values()),
        "tool_calls_by_name": dict(tools),
        "tool_errors": tool_errors,
        "input_tokens": usage["input"],
        "output_tokens": usage["output"],
        "cache_read_tokens": usage["cacheRead"],
        "cache_write_tokens": usage["cacheWrite"],
        "reasoning_tokens": usage["reasoning"],
        "total_tokens": usage["totalTokens"],
        "cost_usd": round(cost, 6),
        "stop_reasons": dict(stop_reasons),
        "error_message": error_message,
        "transport_failures": transport_failures,
        "compactions": compactions,
        "duration_seconds": (max(timestamps) - min(timestamps)).total_seconds() if len(timestamps) > 1 else None,
        "bash_commands": bash_commands,
        "bash_search_commands": dict(search_hits),
        "read_paths": normalized_reads,
        "ran_check_script": any("scripts/check.py" in c.replace("\\", "/") for c in bash_commands),
        "ran_pytest": any("pytest" in c for c in bash_commands),
        "read_docs": sorted({p for p in normalized_reads if "docs/" in p or p.endswith(("README.md", "CONTRIBUTING.md"))}),
        "skill_file_read": any(p.endswith("SKILL.md") for p in normalized_reads),
        "final_text": final_text[-2000:],
    }
