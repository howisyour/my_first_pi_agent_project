/**
 * Turn Pi's `--mode json` event stream into an OpenTelemetry trace (Day 20).
 *
 *   node pi-trace.mjs <trace-out.json> -- <pi args...>
 *
 * Pi 0.84.3 declares a span vocabulary (pi.harness.*, pi.ai.*) but nothing emits it yet,
 * and AgentHarness — the layer that accepts a TelemetryContext — is still a stub. So this
 * wrapper reconstructs the same vocabulary from the outside: it timestamps each event as it
 * arrives and opens/closes spans through the adapter in otel-adapter.mjs.
 *
 * Events carry no timestamps, so every duration here is measured at the moment the line
 * reaches this process. That includes stream transport, which is exactly what we want for
 * "where did the wall clock go", and is not a substitute for spans emitted inside Pi.
 */

import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";

import { InMemorySpanExporter, SimpleSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";

import { createOtelTelemetry } from "./otel-adapter.mjs";

const separator = process.argv.indexOf("--");
if (separator === -1) {
  console.error("usage: node pi-trace.mjs <trace-out.json> -- <pi args...>");
  process.exit(2);
}
const outPath = path.resolve(process.argv[2]);
const piArgs = process.argv.slice(separator + 1);
const cliJs =
  process.env.PI_CLI_JS ??
  path.join(
    process.env.APPDATA ?? "",
    "npm/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js",
  );

const exporter = new InMemorySpanExporter();
const tracerProvider = new NodeTracerProvider({ spanProcessors: [new SimpleSpanProcessor(exporter)] });
const telemetry = createOtelTelemetry(tracerProvider.getTracer("pi-trace"));

/**
 * The contract is callback-based: a span stays open until the callback's promise settles.
 * An event stream needs the opposite shape, so hold the promise and resolve it on the
 * matching "end" event.
 */
function openSpan(parent, name, attributes) {
  let release;
  const pending = new Promise((resolve) => {
    release = resolve;
  });
  let handle;
  const owner = parent ?? telemetry.context;
  owner.startSpan({ name, attributes }, (span) => {
    handle = span;
    return pending;
  });
  return {
    span: handle,
    close(endAttributes) {
      if (endAttributes) handle?.setAttributes(endAttributes);
      release();
    },
  };
}

const child = spawn(process.execPath, [cliJs, ...piArgs], {
  stdio: ["ignore", "pipe", "inherit"],
  env: process.env,
});

let run = null;
let turn = null;
let message = null;
const tools = new Map();
let usage = null;

const rl = readline.createInterface({ input: child.stdout });
rl.on("line", (line) => {
  if (!line.trim()) return;
  let event;
  try {
    event = JSON.parse(line);
  } catch {
    return;
  }
  switch (event.type) {
    case "agent_start":
      run = openSpan(null, "pi.harness.run", { "pi.harness.lane": "main" });
      break;
    case "turn_start":
      turn = openSpan(run?.span, "pi.harness.turn");
      break;
    case "message_start":
      if (event.message?.role === "assistant") {
        message = openSpan(turn?.span ?? run?.span, "pi.ai.request");
      }
      break;
    case "message_update":
      if (event.usage) usage = event.usage;
      break;
    case "message_end": {
      const ended = event.message ?? {};
      if (ended.role !== "assistant" || !message) break;
      const used = ended.usage ?? usage ?? {};
      message.close({
        "pi.ai.provider": ended.provider,
        "pi.ai.model": ended.model,
        "pi.ai.response.stop_reason": ended.stopReason,
        "pi.ai.usage.input_tokens": used.input,
        "pi.ai.usage.output_tokens": used.output,
        "pi.ai.usage.cache_read_tokens": used.cacheRead,
        "pi.ai.usage.reasoning_tokens": used.reasoning,
        "pi.ai.usage.cost": used.cost?.total,
      });
      message = null;
      break;
    }
    case "tool_execution_start":
      tools.set(
        event.toolCallId,
        openSpan(turn?.span ?? run?.span, "pi.harness.tool", { "pi.harness.tool.name": event.toolName }),
      );
      break;
    case "tool_execution_end": {
      const tool = tools.get(event.toolCallId);
      if (!tool) break;
      tool.close({ "pi.harness.tool.is_error": Boolean(event.isError) });
      tools.delete(event.toolCallId);
      break;
    }
    case "turn_end":
      turn?.close();
      turn = null;
      break;
    case "agent_end":
      for (const tool of tools.values()) tool.close();
      tools.clear();
      message?.close();
      turn?.close();
      run?.close({ "pi.harness.will_retry": Boolean(event.willRetry) });
      run = null;
      break;
    default:
      break;
  }
});

child.on("close", async (code) => {
  message?.close();
  turn?.close();
  run?.close();
  await new Promise((resolve) => setTimeout(resolve, 50));

  const toMs = ([seconds, nanos]) => seconds * 1000 + nanos / 1e6;
  const spans = exporter.getFinishedSpans().map((span) => ({
    name: span.name,
    spanId: span.spanContext().spanId,
    parentSpanId: span.parentSpanContext?.spanId ?? null,
    startMs: toMs(span.startTime),
    durationMs: Number(toMs(span.duration).toFixed(1)),
    attributes: span.attributes,
  }));
  spans.sort((a, b) => a.startMs - b.startMs);
  const origin = spans.length > 0 ? spans[0].startMs : 0;
  for (const span of spans) span.startMs = Number((span.startMs - origin).toFixed(1));

  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, `${JSON.stringify({ exitCode: code, spans }, null, 2)}\n`, "utf8");
  const counts = spans.reduce((acc, span) => ({ ...acc, [span.name]: (acc[span.name] ?? 0) + 1 }), {});
  console.log(`exit ${code}, ${spans.length} spans`, counts, `-> ${outPath}`);
  await tracerProvider.shutdown();
});
