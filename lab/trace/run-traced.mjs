/**
 * Run a real Pi agent with OpenTelemetry tracing attached (Day 20).
 *
 *   node run-traced.mjs <workdir> [prompt] [out.json]
 *
 * Pi's CLI never exposes its telemetry context, so this builds the harness directly:
 * pi-agent-core's AgentHarness accepts `context`, and coding-agent's ModelRuntime and
 * tool factories supply the same auth and tools the CLI uses.
 */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { AgentHarness, InMemorySessionRepo } from "@earendil-works/pi-agent-core";
import { createCodingTools, ModelRuntime } from "@earendil-works/pi-coding-agent";
import { InMemorySpanExporter, SimpleSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";

import { createOtelTelemetry } from "./otel-adapter.mjs";

const workdir = path.resolve(process.argv[2] ?? process.cwd());
const prompt = process.argv[3] ?? "跑 python -m pytest，告訴我哪一個測試失敗以及原因。不要修改任何檔案。";
const outPath = path.resolve(process.argv[4] ?? "trace.json");
const agentDir = process.env.PI_CODING_AGENT_DIR ?? path.join(os.homedir(), ".pi", "agent");
const providerId = process.env.PI_PROVIDER ?? "openai-codex";
const modelId = process.env.PI_MODEL ?? "gpt-5.6-luna";

const exporter = new InMemorySpanExporter();
const tracerProvider = new NodeTracerProvider({ spanProcessors: [new SimpleSpanProcessor(exporter)] });
const telemetry = createOtelTelemetry(tracerProvider.getTracer("pi-harness-trace"));

const modelRuntime = await ModelRuntime.create({ authPath: path.join(agentDir, "auth.json") });
const model = modelRuntime.getModel(providerId, modelId);
if (!model) throw new Error(`model not found: ${providerId}/${modelId}`);

const session = await new InMemorySessionRepo().create();
const harness = new AgentHarness({
  session,
  models: modelRuntime,
  model,
  thinkingLevel: "off",
  tools: createCodingTools(workdir),
  activeToolNames: ["read", "bash"],
  systemPrompt: "You are a coding assistant. Use the tools to answer. Be concise.",
  context: telemetry.context,
});

const started = Date.now();
const result = await harness.prompt(prompt);
const wallMs = Date.now() - started;

const hrToMs = ([seconds, nanos]) => seconds * 1000 + nanos / 1e6;
const spans = exporter.getFinishedSpans().map((span) => ({
  name: span.name,
  spanId: span.spanContext().spanId,
  parentSpanId: span.parentSpanContext?.spanId ?? null,
  startMs: hrToMs(span.startTime),
  durationMs: Number(hrToMs(span.duration).toFixed(2)),
  status: span.status.code === 2 ? "error" : "ok",
  attributes: span.attributes,
  events: span.events.map((event) => ({ name: event.name, attributes: event.attributes })),
}));
spans.sort((a, b) => a.startMs - b.startMs);
const origin = spans.length > 0 ? spans[0].startMs : 0;
for (const span of spans) span.startMs = Number((span.startMs - origin).toFixed(2));

fs.writeFileSync(
  outPath,
  `${JSON.stringify({ model: `${providerId}/${modelId}`, prompt, wallMs, stopReason: result?.stopReason, spans }, null, 2)}\n`,
  "utf8",
);

const byName = spans.reduce((acc, span) => ({ ...acc, [span.name]: (acc[span.name] ?? 0) + 1 }), {});
console.log(`wall ${wallMs} ms, ${spans.length} spans:`, byName);
console.log(`written to ${outPath}`);
await tracerProvider.shutdown();
