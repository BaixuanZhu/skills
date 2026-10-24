/**
 * PostToolUse hook（Write / Edit）—— Backlog 统计一致性看守
 *
 * 职责单一：PRODUCT-BACKLOG.md 被写过之后重算一遍，和人写的「## 统计」段比对。
 * 不一致就把完整正确数字喂回去，让 agent 直接整块替换。
 *
 * 为什么需要它：技能 §七 规定「从阶段表重新全量统计，禁止在旧数字上增量加减」，
 * 但实测下来 agent 每次都是现场写一段统计脚本——每次都不一样，可能漏行、可能做加减。
 * 计算这件事本来就不该交给模型。
 *
 * 为什么不阻断保留退出码 0：
 *   PostToolUse 无法撤销已写入的内容，exit 2 也只是把 stderr 递给模型。
 *   数字对不上属于硬错误（不是建议），所以用 exit 2 让它显眼；正常时完全静默。
 *
 * fail-open：脚本随插件分发到别人机器上，任何未预期异常都必须变成沉默，
 * 不能因为 hook 自己出错就让每次编辑都弹一条错误。
 */
import { existsSync, readFileSync } from 'node:fs';
import { isAbsolute, resolve } from 'node:path';
import { computeStats, extractTotals, parseBacklog, renderStats } from './backlog-parse.mjs';

process.on('uncaughtException', () => process.exit(0));
process.on('unhandledRejection', () => process.exit(0));

const TARGET = /(^|[\\/])PRODUCT-BACKLOG\.md$/i;

let raw = '';
process.stdin.on('data', (d) => (raw += d));

process.stdin.on('end', () => {
  let payload;
  try {
    payload = JSON.parse(raw || '{}');
  } catch {
    process.exit(0); // 输入解析不了，静默放行
  }

  const input = payload.tool_input ?? payload.toolInput ?? {};
  const rawPath = String(input.file_path ?? input.filePath ?? input.path ?? '');
  if (!TARGET.test(rawPath)) process.exit(0);

  const cwd = payload.cwd || process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const file = isAbsolute(rawPath) ? rawPath : resolve(cwd, rawPath);

  let text = '';
  try {
    if (!existsSync(file)) process.exit(0);
    text = readFileSync(file, 'utf8');
  } catch {
    process.exit(0);
  }

  const { rows, statsText } = parseBacklog(text);
  if (rows.length === 0) process.exit(0); // 不是本技能的格式，不插手

  const stats = computeStats(rows);
  const body = renderStats(stats);

  // 缺统计段：先提示补上，不算错误（第一次写 Backlog 时可能还没加）
  if (!statsText.trim()) {
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PostToolUse',
          additionalContext:
            `[agile] PRODUCT-BACKLOG.md 没有「## 统计」段。按 §七 要求补一段，内容已算好，直接粘贴：\n${body}`,
        },
      }) + '\n'
    );
    process.exit(0);
  }

  const found = extractTotals(statsText);
  if (!found) process.exit(0); // 统计段格式不可识别 → 不误报
  if (found.total === stats.total && found.points === stats.points) process.exit(0);

  // 数字对不上：这是硬错误，喂回完整正确值
  const diff = [
    `[agile] Backlog 统计与阶段表不符。`,
    `  统计段写的：${found.total} 条 / ${found.points} 点`,
    `  按阶段表重算：${stats.total} 条 / ${stats.points} 点`,
    `差 ${stats.total - found.total} 条 / ${stats.points - found.points} 点。`,
    ``,
    `按 §七「全量重算，禁止增量加减」，用下面整块替换「## 统计」段的内容（不要只改数字）：`,
    body,
  ].join('\n');

  process.stderr.write(diff + '\n');
  process.exit(2);
});
