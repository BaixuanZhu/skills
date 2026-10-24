/**
 * SessionStart hook —— 注入敏捷状态摘要
 *
 * 解决的问题：技能要 agent 主动读才生效。实测（.claude/rules 那次）证明，
 * 文件存在但没被读时，行为与完全没有该文件一致。agile-docs/ 里全是状态，
 * 每次会话开头把「做到哪、哪些没拍板」摆到桌上，比指望 agent 自己去翻可靠。
 *
 * 三个平台都能用：Claude Code / ZCode 走 additionalContext，Codex 的 SessionStart
 * 同样支持注入上下文。所以这是 Codex 上唯一能生效的兜底——它拦不到 Write，
 * 但下次会话开头会看到统计不一致。
 *
 * 只读不写，任何异常一律静默。
 */
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { computeStats, extractTotals, parseBacklog } from './backlog-parse.mjs';

process.on('uncaughtException', () => process.exit(0));
process.on('unhandledRejection', () => process.exit(0));

const read = (p) => {
  try {
    return readFileSync(p, 'utf8');
  } catch {
    return null;
  }
};

const listDir = (p) => {
  try {
    return readdirSync(p);
  } catch {
    return [];
  }
};

let raw = '';
process.stdin.on('data', (d) => (raw += d));

process.stdin.on('end', () => {
  let payload = {};
  try {
    payload = JSON.parse(raw || '{}');
  } catch {
    /* 用默认 cwd */
  }

  const cwd = payload.cwd || process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const docs = join(cwd, 'agile-docs');
  const backlogPath = join(docs, 'PRODUCT-BACKLOG.md');

  // 项目没启用敏捷套件 → 完全沉默，不要说一句「我没找到」
  if (!existsSync(backlogPath)) process.exit(0);

  const parts = [];

  // ── Sprint ────────────────────────────────────────────────────────────
  const sprintDirs = [join(cwd, 'sprints'), join(docs, 'sprints')];
  const sprintFiles = [];
  for (const dir of sprintDirs) {
    for (const name of listDir(dir)) {
      if (/^sprint-\d{3}-\d+\.md$/.test(name)) sprintFiles.push({ dir, name });
    }
  }
  sprintFiles.sort((a, b) => b.name.localeCompare(a.name));
  const latest = sprintFiles[0];
  if (latest) {
    const text = read(join(latest.dir, latest.name)) ?? '';
    const status = text.match(/^\s*-\s*状态[:：]\s*(.+)$/m)?.[1]?.trim();
    const period = text.match(/^\s*-\s*周期[:：]\s*(.+)$/m)?.[1]?.trim();
    const seq = latest.name.match(/^sprint-(\d{3})/)?.[1];
    const bits = [`Sprint ${seq}`];
    if (status) bits.push(status);
    if (period) bits.push(`(${period})`);
    parts.push(bits.join(' '));
  }

  // ── 未处理回填 ────────────────────────────────────────────────────────
  const pending = [];
  for (const dir of sprintDirs) {
    for (const name of listDir(dir)) {
      if (name.endsWith('.done.yaml')) pending.push(name.replace('.done.yaml', ''));
    }
  }
  if (pending.length) parts.push(`待回填 ${pending.length} 个（${pending.join('、')}）`);

  // ── Backlog ───────────────────────────────────────────────────────────
  const backlogText = read(backlogPath);
  if (backlogText) {
    const { rows, statsText } = parseBacklog(backlogText);
    if (rows.length) {
      const s = computeStats(rows);
      parts.push(`Backlog ${s.total} 条 / ${s.points} 点（已确认 ${s.confirmed}）`);

      const found = extractTotals(statsText);
      if (found && (found.total !== s.total || found.points !== s.points)) {
        parts.push(
          `⚠ 统计段写的是 ${found.total} 条 / ${found.points} 点，按阶段表重算应为 ` +
            `${s.total} 条 / ${s.points} 点——下次改动 Backlog 时按全量重算修正`
        );
      }
    }
  }

  // ── ADR ───────────────────────────────────────────────────────────────
  const adrText = read(join(docs, 'ADR.md'));
  if (adrText) {
    // 按条目切段再判断，不能数全文出现次数：单条 ADR 里 Proposed 会出现多次（状态行 + 正文），
    // 数出来会比 ADR 总数还大。段 0 是索引/说明区，丢掉。
    const blocks = adrText.split(/^#{2,4}\s+ADR-\d+.*$/m).slice(1);
    const proposed = blocks.filter((b) => /\bProposed\b/.test(b)).length;
    if (blocks.length) {
      parts.push(
        proposed
          ? `ADR ${blocks.length} 条（${proposed} 条 Proposed 待拍板）`
          : `ADR ${blocks.length} 条`
      );
    }
  }

  if (!parts.length) process.exit(0);

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext: `[agile] ${parts.join('｜')}`,
      },
    }) + '\n'
  );
  process.exit(0);
});
