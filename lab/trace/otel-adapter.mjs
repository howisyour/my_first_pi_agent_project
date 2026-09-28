/**
 * An OpenTelemetry adapter for Pi's vendor-neutral telemetry contract (Day 20).
 *
 * Pi hands every layer a `TelemetryContext` and never depends on a telemetry backend.
 * This file is the bridge: it implements that contract on top of an OpenTelemetry tracer.
 *
 * The contract's rules (docs: @earendil-works/pi-telemetry README, "Adapter Contract"):
 *   - call the callback synchronously, exactly once;
 *   - return the callback's value; a synchronous throw becomes a rejected promise;
 *   - keep the span open until a returned promise settles;
 *   - normal completion is `ok`, throws are errors, unless a status was set explicitly;
 *   - recording methods are synchronous, passive, non-throwing, and inert after settlement;
 *   - a backend failure must never break the business callback.
 */

import { context as otelContext, SpanStatusCode, trace } from "@opentelemetry/api";

function definedOnly(attributes) {
  const out = {};
  for (const [key, value] of Object.entries(attributes ?? {})) {
    if (value !== undefined) out[key] = value;
  }
  return out;
}

/** Runs the callback exactly once without recording anything, keeping the contract's settlement rules. */
function runInert(callback) {
  let result;
  try {
    result = callback(INERT_SPAN);
  } catch (thrown) {
    return Promise.reject(thrown);
  }
  return result;
}

const INERT_SPAN = Object.freeze({
  setAttributes() {},
  addEvent() {},
  setStatus() {},
  startSpan: (_options, callback) => runInert(callback),
});

function describeThrown(thrown) {
  try {
    return { name: thrown?.name ?? "Error", message: thrown?.message ?? String(thrown) };
  } catch {
    return { name: "Error", message: "unreadable error" };
  }
}

export function createOtelTelemetry(tracer) {
  const records = [];
  let startSequence = 0;
  let endSequence = 0;

  function settle(record, span, thrown, hasThrown) {
    if (!record || record.settled) return;
    record.settled = true;
    record.endSequence = ++endSequence;
    if (hasThrown && !record.explicitStatus) {
      record.status = { status: "error", error: describeThrown(thrown) };
    }
    try {
      if (record.status.status === "error") {
        span.setStatus({ code: SpanStatusCode.ERROR, message: record.status.error?.message });
        span.setAttributes(definedOnly({ "pi.error.name": record.status.error?.name }));
      } else {
        span.setStatus({ code: SpanStatusCode.OK });
      }
      span.end();
    } catch {
      // A backend failure must not change what the business code does.
    }
  }

  function makeSpan(span, spanContext, record) {
    return {
      // Every recording method is passive: a hostile payload or a backend failure is swallowed,
      // and a call that fails is ignored whole rather than applied halfway.
      setAttributes(attributes) {
        if (record.settled) return;
        try {
          const clean = definedOnly(attributes);
          span.setAttributes(clean);
          Object.assign(record.attributes, clean);
        } catch {
          /* ignored atomically */
        }
      },
      addEvent(name, attributes) {
        if (record.settled) return;
        try {
          const clean = definedOnly(attributes);
          const eventName = String(name);
          span.addEvent(eventName, clean);
          record.events.push({ name: eventName, attributes: clean });
        } catch {
          /* ignored atomically */
        }
      },
      setStatus(status) {
        if (record.settled) return;
        try {
          const next =
            status?.status === "error"
              ? {
                  status: "error",
                  ...(status.error
                    ? { error: { name: status.error.name, message: status.error.message } }
                    : {}),
                }
              : { status: "ok" };
          record.status = next;
          record.explicitStatus = true;
        } catch {
          /* ignored atomically */
        }
      },
      startSpan(options, callback) {
        if (record.settled) return runInert(callback);
        return start(spanContext, record.id, options, callback);
      },
    };
  }

  function start(parentContext, parentId, options, callback) {
    let span;
    let record;
    let wrapper = INERT_SPAN;
    try {
      const attributes = definedOnly(options?.attributes);
      span = tracer.startSpan(options?.name ?? "unnamed", { attributes }, parentContext);
      record = {
        id: ++startSequence,
        parentId,
        name: options?.name ?? "unnamed",
        attributes: { ...attributes },
        events: [],
        status: { status: "ok" },
        explicitStatus: false,
        settled: false,
        endSequence: undefined,
      };
      records.push(record);
      wrapper = makeSpan(span, trace.setSpan(parentContext, span), record);
    } catch {
      // Recording is best-effort: fall through with an inert span so the callback still runs once.
    }

    let result;
    try {
      result = callback(wrapper);
    } catch (thrown) {
      settle(record, span, thrown, true);
      return Promise.reject(thrown);
    }

    if (result && typeof result.then === "function") {
      return result.then(
        (value) => {
          settle(record, span, undefined, false);
          return value;
        },
        (thrown) => {
          settle(record, span, thrown, true);
          throw thrown;
        },
      );
    }

    settle(record, span, undefined, false);
    return result;
  }

  return {
    /** The object Pi receives as its `TelemetryContext`. */
    context: {
      startSpan(options, callback) {
        return start(otelContext.active(), null, options, callback);
      },
    },
    /** Normalized snapshots in span-start order, matching pi-telemetry's RecordedTelemetrySpan. */
    getSpans() {
      return records.map((record) => ({
        id: record.id,
        parentId: record.parentId,
        name: record.name,
        attributes: { ...record.attributes },
        events: record.events.map((event) => ({ name: event.name, attributes: { ...event.attributes } })),
        status: record.status,
        settled: record.settled,
        ...(record.endSequence === undefined ? {} : { endSequence: record.endSequence }),
      }));
    },
  };
}
