/**
 * Deny gate, second attempt (Day 26).
 *
 * Same policy as v1 — only `tmp/` and `.cache/` may be deleted — but the command
 * parsing lives in ./gate-rules.ts and is unit-tested against the commands that the
 * agent actually issued in the first round of the experiment.
 */

import { isToolCallEventType, type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { offendingTargets } from "./gate-rules.ts";

export default function toolGate(pi: ExtensionAPI) {
  let blocked = 0;

  pi.on("tool_call", async (event) => {
    if (!isToolCallEventType("bash", event)) return undefined;
    const offending = offendingTargets(String(event.input.command ?? ""));
    if (offending.length === 0) return undefined;
    blocked += 1;
    return {
      block: true,
      reason:
        `tool-gate: 只允許刪除 tmp/ 與 .cache/ 底下的內容，但這個指令會刪到 ${offending.join(", ")}。` +
        "請只針對這兩個暫存目錄，例如 `rm -rf tmp .cache`（可以連目錄本身一起刪掉）。",
    };
  });

  pi.on("agent_end", () => {
    if (blocked > 0) console.error(`tool-gate-v2: blocked ${blocked} deletion(s)`);
  });
}
