/**
 * Runs Pi's own telemetry adapter conformance suite against the OpenTelemetry adapter,
 * and checks that the real OTel exporter saw the same spans.
 *
 *   node --test lab/trace/
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { createTelemetryAdapterConformance } from "@earendil-works/pi-telemetry/testing";
import { InMemorySpanExporter, SimpleSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";

import { createOtelTelemetry } from "./otel-adapter.mjs";

function newFixtureParts() {
  const exporter = new InMemorySpanExporter();
  const provider = new NodeTracerProvider({ spanProcessors: [new SimpleSpanProcessor(exporter)] });
  const adapter = createOtelTelemetry(provider.getTracer("pi-harness-trace"));
  return { exporter, provider, adapter };
}

const conformance = createTelemetryAdapterConformance(async () => {
  const { exporter, provider, adapter } = newFixtureParts();
  return {
    context: adapter.context,
    getSpans: async () => adapter.getSpans(),
    async [Symbol.asyncDispose]() {
      await provider.shutdown();
      exporter.reset();
    },
  };
});

for (const group of new Set(conformance.map((testCase) => testCase.group))) {
  describe(`conformance: ${group}`, () => {
    for (const testCase of conformance.filter((candidate) => candidate.group === group)) {
      it(testCase.name, () => testCase.run());
    }
  });
}

describe("OpenTelemetry side", () => {
  it("exports the same tree to a real OTel exporter", async () => {
    const { exporter, provider, adapter } = newFixtureParts();
    await adapter.context.startSpan({ name: "pi.harness.run", attributes: { "pi.harness.lane": "main" } },
      async (run) => {
        await run.startSpan({ name: "pi.harness.turn" }, async (turn) => {
          turn.addEvent("pi.ai.retry", { attempt: 1 });
          await turn.startSpan({ name: "pi.ai.request", attributes: { "pi.ai.model": "demo" } }, async (request) => {
            request.setAttributes({ "pi.ai.usage.input_tokens": 1200 });
          });
        });
      });

    const finished = exporter.getFinishedSpans();
    assert.deepEqual(finished.map((span) => span.name).sort(),
      ["pi.ai.request", "pi.harness.run", "pi.harness.turn"]);

    const request = finished.find((span) => span.name === "pi.ai.request");
    const turn = finished.find((span) => span.name === "pi.harness.turn");
    const run = finished.find((span) => span.name === "pi.harness.run");

    // Parentage survives the bridge: request -> turn -> run.
    assert.equal(request.parentSpanContext?.spanId, turn.spanContext().spanId);
    assert.equal(turn.parentSpanContext?.spanId, run.spanContext().spanId);
    // Start and completion attributes land on the same backend span.
    assert.equal(request.attributes["pi.ai.model"], "demo");
    assert.equal(request.attributes["pi.ai.usage.input_tokens"], 1200);
    assert.equal(turn.events[0].name, "pi.ai.retry");
    // Every span is inside its parent's window.
    assert.ok(request.endTime <= turn.endTime);

    await provider.shutdown();
  });
});
