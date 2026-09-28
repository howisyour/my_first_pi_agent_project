/**
 * A deny gate on the tool call boundary (Day 25).
 *
 * Pi fires `tool_call` after `tool_execution_start` and before the tool runs, and a handler
 * can return `{ block: true, reason }` to stop it. This one refuses deletions that touch
 * anything outside the known scratch directories, and tells the agent why.
 */

import { isToolCallEventType, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

/** Only these may be deleted. Everything else is project content. */
const DELETABLE = [/(^|[\s"'./\\])tmp([\\/]|\s|$)/i, /(^|[\s"'./\\])\.cache([\\/]|\s|$)/i];

const DELETE_COMMAND = /(^|[\s;|&(])(rm|rmdir|del|erase|Remove-Item|ri)\b/i;

function isDeletion(command: string): boolean {
  return DELETE_COMMAND.test(command);
}

function targetsOnlyScratch(command: string): boolean {
  // Strip the command word, keep the operands, and drop flags.
  const operands = command
    .replace(DELETE_COMMAND, " ")
    .split(/\s+/)
    .filter((token) => token.length > 0 && !token.startsWith("-"));
  if (operands.length === 0) return false;
  return operands.every((operand) => DELETABLE.some((allowed) => allowed.test(operand)));
}

export default function toolGate(pi: ExtensionAPI) {
  let blocked = 0;

  pi.on("tool_call", async (event) => {
    if (isToolCallEventType("bash", event)) {
      const command = String(event.input.command ?? "");
      if (isDeletion(command) && !targetsOnlyScratch(command)) {
        blocked += 1;
        return {
          block: true,
          reason:
            "tool-gate: 只允許刪除 tmp/ 與 .cache/ 底下的內容。" +
            "這個指令會動到其他路徑，請改成只針對暫存目錄。",
        };
      }
    }
    return undefined;
  });

  pi.on("agent_end", () => {
    if (blocked > 0) console.error(`tool-gate: blocked ${blocked} deletion(s)`);
  });
}
