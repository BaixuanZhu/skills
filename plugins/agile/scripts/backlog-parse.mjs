/**
 * PRODUCT-BACKLOG.md 解析与统计（backlog-stats / session-state 共用）
 *
 * 契约来源：agile-backlog/references/backlog-rules.md §七 表格机读契约
 *   列名严格固定：| ID | 标题 | 类型 | 仓库 | 点 | 优先级 | 状态 | 关联 | 来源/依据 | 已确认 |
 *   统计规则：从阶段表重新全量统计（覆盖式重算），禁止在旧数字上增量加减
 *
 * 存在的理由：这条规则原先只写在技能里，靠 agent 每次现场写脚本兑现。
 * 现场写的脚本每次都不同、可能少算行、也可能在旧数字上做加减。挪到这里就固定了。
 *
 * 容错原则：解析不出任何条目 → 视为「不是本技能管的文件」，调用方静默放行。
 * hook 误报比不报更糟，所以宁可漏报也不要在格式漂移时喊狼来了。
 */

const ID_RE = /^[TF]-\d{2,4}$/;
const POINT_RE = /^\d+(?:\.\d+)?$/;

/** 解析文件，返回 { rows, statsText, warnings } */
export function parseBacklog(text) {
  const lines = String(text ?? '').split(/\r?\n/);
  const rows = [];
  const warnings = [];
  let phase = null;
  let inStats = false;
  let statsLines = [];

  for (const line of lines) {
    // 标题行：切换「阶段 N」上下文，或进入 / 离开统计段
    const header = line.match(/^#{2,4}\s+(.+)$/);
    if (header) {
      const title = header[1].trim();
      const pm = title.match(/^阶段\s*(\d+)/);
      if (pm) phase = Number(pm[1]);
      inStats = /^统计/.test(title);
      if (inStats) statsLines = [];
      continue;
    }
    if (inStats) {
      statsLines.push(line);
      continue;
    }
    if (!line.startsWith('|')) continue;

    const cells = line.split('|').slice(1, -1).map((s) => s.trim());
    if (cells.length < 7) continue; // 表头 / 分隔行 / 无关表格
    const id = cells[0];
    if (!ID_RE.test(id)) continue;

    // 用「首列 = ID、末列 = 已确认」定位，中间列数漂移也不影响取这两个端点值
    const confirmed = cells[cells.length - 1];
    const pointsRaw = cells[4] ?? '';

    if (cells.length !== 10) {
      warnings.push(`${id} 列数 ${cells.length}，契约要求 10 列`);
    }
    if (!POINT_RE.test(pointsRaw)) {
      warnings.push(`${id} 点数「${pointsRaw}」不是数字，按 0 计`);
    }

    rows.push({
      id,
      type: cells[2] ?? '',
      points: POINT_RE.test(pointsRaw) ? Number(pointsRaw) : 0,
      priority: cells[5] ?? '',
      status: cells[6] ?? '',
      confirmed,
      phase: phase ?? 0,
    });
  }

  return { rows, statsText: statsLines.join('\n'), warnings };
}

/** 全量重算。已撤回的条目按 §七 排除出排序与统计（留痕不入账）。 */
export function computeStats(rows) {
  const live = rows.filter((r) => r.status !== '已撤回');
  const group = (keyFn) => {
    const map = new Map();
    for (const r of live) {
      const k = keyFn(r);
      const cur = map.get(k) ?? { count: 0, points: 0 };
      cur.count += 1;
      cur.points += r.points;
      map.set(k, cur);
    }
    return map;
  };

  const total = live.length;
  const points = live.reduce((s, r) => s + r.points, 0);
  const confirmed = live.filter((r) => r.confirmed === '✓').length;

  return {
    total,
    points,
    confirmed,
    withdrawn: rows.length - live.length,
    byType: group((r) => r.type || '未标'),
    byPhase: group((r) => r.phase),
    byPriority: group((r) => r.priority || '未标'),
    byStatus: group((r) => r.status || '未标'),
  };
}

// 状态分组只关心条数：已完成/已撤回的点数没有解释价值，写出来反而让人以为要合计
const fmtGroup = (map, keyFmt = (k) => k, withPoints = true) =>
  [...map.entries()]
    .sort((a, b) => String(a[0]).localeCompare(String(b[0]), 'zh', { numeric: true }))
    .map(([k, v]) => `${keyFmt(k)} = ${v.count} 条${withPoints ? ` / ${v.points} 点` : ''}`)
    .join('；');

/** 渲染成可直接粘贴的统计段（不含标题行，标题由调用方按需加） */
export function renderStats(s) {
  const lines = [`- 条目：${s.total} 条 / ${s.points} 点`];
  if (s.byType.size) lines.push(`- 按类型：${fmtGroup(s.byType)}`);
  if (s.byPhase.size) lines.push(`- 按阶段：${fmtGroup(s.byPhase, (k) => `阶段 ${k}`)}`);
  if (s.byPriority.size) lines.push(`- 按优先级：${fmtGroup(s.byPriority)}`);
  if (s.byStatus.size) lines.push(`- 按状态：${fmtGroup(s.byStatus, (k) => k, false)}`);
  lines.push(`- 已确认：${s.confirmed} 条 ✓ / ${s.total - s.confirmed} 条待确认`);
  if (s.withdrawn) lines.push(`- 已撤回：${s.withdrawn} 条（不计入以上统计）`);
  return lines.join('\n');
}

/**
 * 从统计段里抽出「总数 / 总点数」。
 * 先按约定格式抓；抓不到就退化成「统计段里是否同时出现两个数字」——格式漂移时不误报。
 * 返回 null 表示不可识别，调用方应静默放行。
 */
export function extractTotals(statsText) {
  const text = String(statsText ?? '');
  if (!text.trim()) return null;

  const strict = text.match(/条目[：:]\s*\*{0,2}\s*(\d+)\s*条\s*\/\s*(\d+)\s*点/);
  if (strict) return { total: Number(strict[1]), points: Number(strict[2]) };

  const nums = [...text.matchAll(/(\d+)\s*条/g)].map((m) => Number(m[1]));
  const pts = [...text.matchAll(/(\d+)\s*点/g)].map((m) => Number(m[1]));
  if (nums.length && pts.length) return { total: nums[0], points: pts[0], loose: true };

  return null;
}
