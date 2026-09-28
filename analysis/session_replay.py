"""Rebuild a Pi session's state from its event log (Day 29).

  python -m analysis.session_replay <session.jsonl>              # final state
  python -m analysis.session_replay <session.jsonl> --at <id>    # state as of one event
  python -m analysis.session_replay <session.jsonl> --check <run.json>

A session file is an append-only log of events, each carrying `id` and `parentId`. The state
the harness sends to the model is not stored anywhere — it is the fold of that log along the
parent chain. This reproduces the fold outside Pi, which is what makes the recorded runs
auditable (and what Day 18/20/26 were quietly relying on).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class State:
    """Everything the fold produces. `messages` is what a resumed run would replay."""

    version: int | None = None
    cwd: str | None = None
    model: str | None = None
    provider: str | None = None
    thinking: str | None = None
    messages: list[dict] = field(default_factory=list)
    compactions: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0

    @property
    def turns(self) -> int:
        return sum(1 for m in self.messages if m.get("role") == "assistant")

    @property
    def tool_calls(self) -> int:
        return sum(
            1
            for m in self.messages
            if m.get("role") == "assistant"
            for block in m.get("content", [])
            if block.get("type") == "toolCall"
        )


def read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def chain_to(events: list[dict], event_id: str | None) -> list[dict]:
    """The events on the parent chain ending at `event_id` (default: the last event).

    The log is a tree, not a line: retrying or editing a turn appends a sibling instead of
    rewriting history. Walking parents is what picks one branch out of it.
    """
    by_id = {event["id"]: event for event in events if "id" in event}
    node = by_id.get(event_id) if event_id else (events[-1] if events else None)
    if event_id and node is None:
        raise SystemExit(f"no event with id {event_id}")
    branch: list[dict] = []
    while node is not None:
        branch.append(node)
        node = by_id.get(node.get("parentId"))
    return list(reversed(branch))


def reduce_events(events: list[dict]) -> State:
    """One case per event type — this is the whole reducer."""
    state = State()
    for event in events:
        kind = event.get("type")
        if kind == "session":
            state.version, state.cwd = event.get("version"), event.get("cwd")
        elif kind == "model_change":
            state.model, state.provider = event.get("modelId"), event.get("provider")
        elif kind == "thinking_level_change":
            state.thinking = event.get("thinkingLevel")
        elif kind == "compaction":
            # The summary replaces the history the *next* request sends; the log keeps both.
            state.compactions.append(event["id"])
            state.messages = [{"role": "user", "content": [{"type": "text", "text": event["summary"]}],
                               "synthetic": "compaction"}]
        elif kind == "message":
            message = event["message"]
            state.messages.append(message)
            usage = message.get("usage") or {}
            state.input_tokens += usage.get("input", 0)
            state.output_tokens += usage.get("output", 0)
            state.cache_read += usage.get("cacheRead", 0)
            state.reasoning_tokens += usage.get("reasoning", 0)
            state.cost_usd += (usage.get("cost") or {}).get("total", 0.0)
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("session", type=Path)
    parser.add_argument("--at", help="rebuild the state as of this event id")
    parser.add_argument("--check", type=Path, help="a runs.jsonl record to cross-check the totals against")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    events = read_events(args.session)
    branch = chain_to(events, args.at)
    # The `session` header has no parent and is not part of the chain; fold it in separately.
    header = [event for event in events if event.get("type") == "session"]
    state = reduce_events(header + branch)
    on_branch = {event["id"] for event in branch if "id" in event} | {e["id"] for e in header}
    off_branch = sum(1 for event in events if event.get("id") not in on_branch)

    summary = {
        "session_format": f"v{state.version}",
        "events_in_file": len(events),
        "events_on_branch": len(branch),
        "events_off_branch": off_branch,
        "model": f"{state.provider}/{state.model}",
        "thinking": state.thinking,
        "messages": len(state.messages),
        "turns": state.turns,
        "tool_calls": state.tool_calls,
        "compactions": len(state.compactions),
        "input_tokens": state.input_tokens,
        "cache_read_tokens": state.cache_read,
        "output_tokens": state.output_tokens,
        "reasoning_tokens": state.reasoning_tokens,
        "cost_usd": round(state.cost_usd, 6),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        width = max(len(k) for k in summary)
        for key, value in summary.items():
            print(f"{key.replace('_', ' '):<{width}}  {value}")

    if args.check:
        recorded = json.loads(args.check.read_text(encoding="utf-8"))
        metrics = recorded.get("metrics") or recorded
        deltas = {
            "cost_usd": round(state.cost_usd - metrics["cost_usd"], 8),
            "tool_calls": state.tool_calls - metrics["tool_calls"],
        }
        print("\ncross-check vs recorded metrics:", json.dumps(deltas))
        return 0 if not any(deltas.values()) else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
