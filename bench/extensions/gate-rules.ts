/**
 * Deletion-classification rules for the tool gate (Day 26, v2).
 *
 * Kept free of any Pi imports so it can be unit-tested with plain `node --test`.
 * v1 (tool-gate.ts) got this wrong in two directions on commands the agent really issued:
 *   - false positive: `rm -rf .cache tmp && git status --short && python scripts/check.py`
 *     was blocked, because every token after `&&` was counted as a deletion target;
 *   - false negative: `find .cache tmp -mindepth 1 -delete` was not recognised as a
 *     deletion at all, so the gate had nothing to say about it.
 */

const SCRATCH = [/^\.?[\/]?tmp([\/].*)?$/i, /^\.?[\/]?\.cache([\/].*)?$/i];

const RM_WORD = /^(rm|rmdir|del|erase|Remove-Item|ri)$/i;

/** Split a shell line into the individual commands it runs. */
export function segments(command: string): string[] {
  return command
    .split(/&&|\|\||[;\n|]/)
    .map((segment) => segment.trim())
    .filter((segment) => segment.length > 0);
}

function tokenize(segment: string): string[] {
  const matched = segment.match(/"[^"]*"|'[^']*'|\S+/g) ?? [];
  return matched.map((token) => token.replace(/^["']|["']$/g, ""));
}

/** Drop `2>/dev/null`, `> out.txt`, `2>&1` and friends — they are not deletion targets. */
function stripRedirections(tokens: string[]): string[] {
  const kept: string[] = [];
  for (let i = 0; i < tokens.length; i += 1) {
    const token = tokens[i];
    if (/^\d*(>>|>|<)/.test(token)) {
      if (/^\d*(>>|>|<)$/.test(token)) i += 1; // `> file`: the filename follows
      continue;
    }
    kept.push(token);
  }
  return kept;
}

export function isScratch(operand: string): boolean {
  const cleaned = operand.replace(/[*?]/g, "").replace(/[\/]+$/, "");
  if (cleaned === "" || cleaned === "." || cleaned === "..") return false;
  return SCRATCH.some((allowed) => allowed.test(cleaned));
}

/** What this one command would delete, or null when it deletes nothing. */
export function deletionTargets(segment: string): string[] | null {
  const parts = stripRedirections(tokenize(segment));
  if (parts.length === 0) return null;
  const [head, ...rest] = parts;

  if (RM_WORD.test(head)) {
    return rest.filter((token) => !token.startsWith("-"));
  }

  // `find <paths> ... -delete` and `find <paths> ... -exec rm ...`
  if (/^find$/i.test(head) && (rest.includes("-delete") || rest.some((token) => RM_WORD.test(token)))) {
    const paths: string[] = [];
    for (const token of rest) {
      if (token.startsWith("-")) break;
      paths.push(token);
    }
    return paths.length > 0 ? paths : ["."];
  }

  return null;
}

/** Operands outside the scratch whitelist, across every command in the line. */
export function offendingTargets(command: string): string[] {
  const offending: string[] = [];
  for (const segment of segments(command)) {
    const targets = deletionTargets(segment);
    if (!targets) continue;
    for (const target of targets) {
      if (!isScratch(target)) offending.push(target);
    }
  }
  return offending;
}
