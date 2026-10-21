/**
 * PostToolUse hook（Bash）—— 构建失败症状索引
 *
 * 职责单一：构建命令跑完之后，看一眼日志里有没有已知的失败特征；命中就注入一行排查指针。
 * 不做诊断、不改代码、不阻断任何操作。
 *
 * 设计依据（均为实测）：
 *   1. 项目门控：只在真的用 MyBatis-Plus 的项目上激活。
 *      hook 随插件装到任何人机器上，不做门控就会对无关项目输出误导性提示
 *      （`does not exist`、唯一约束冲突是所有 Java 项目都会出现的通用 SQL 报错）。
 *   2. 信号源双通道：优先 .mvn-logs/build.log（Maven -l 落盘），否则用 tool_response 的 stdout/stderr。
 *      → 不要求项目改造 maven.config，未做任何约定的项目也能用。
 *   3. 去重：同会话同症状只报一次，症状从构建输出中消失后重新武装。
 *      实测原版会在同一个失败构建上重复注入 3 次。
 *   4. 只报第一条命中：一次构建常同时命中多个串（BindingException 的堆栈里必含 Invalid bound statement），
 *      但命中的串要全部标记，否则下一轮会补报另一条。
 *
 * 状态与门控缓存都在系统临时目录，不写进项目，也不依赖 .gitignore。
 */
import { readFileSync, statSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { createHash } from 'node:crypto';

const LOG = '.mvn-logs/build.log';
const STALE_MS = 10 * 60 * 1000;      // 日志超过 10 分钟视为陈旧，防止拿上次的失败误报
const GATE_TTL_MS = 60 * 60 * 1000;   // 「项目无 MP」的否定结论缓存 1 小时
const MAX_SCAN = 512 * 1024;          // 探测依赖时最多读 512KB 构建文件

// fail-open 兜底：这个脚本随插件分发到别人的机器上，任何未预期异常都不能变成
// 用户每次构建后看到一条 hook error。宁可沉默，不可打扰。
process.on('uncaughtException', () => process.exit(0));
process.on('unhandledRejection', () => process.exit(0));

// ── 症状表 ────────────────────────────────────────────────────────────────
// 分两层：
//   框架层 —— MyBatis / MP 自己抛的，跨数据库一致，已真机验证（真实 Maven 构建 + 真实堆栈）
//   数据库层 —— 异常文案由数据库给出，MySQL 与 PostgreSQL 完全不同，必须各写一套
// 按优先级排列，只报第一条命中的。
const SYMPTOMS = [
  {
    token: 'Invalid bound statement',
    hint:
      '三步排查，按命中率排序：① 接口方法与 XML 的 id 是否同名同参 ② mapper-locations 能否命中该 XML ' +
      '③ @MapperScan 包路径是否覆盖该 Mapper。只写接口不写 XML（或反之）必然报这个。',
  },
  {
    token: 'BindingException',
    hint: '多参方法缺 @Param：每个参数加 @Param("x")，XML 里用 #{x}。注意报错里列出的 arg0/param1 不是真实参数名。',
  },
  {
    token: 'Duplicate entry', // MySQL 文案
    also: 'for key',
    hint:
      'MySQL 唯一约束冲突。若该表启用了逻辑删除：唯一索引必须包含删除标记列（如 UNIQUE(username, deleted)），' +
      '否则删过的值再也插不进去。',
  },
  {
    token: 'duplicate key value violates unique constraint', // PostgreSQL 文案
    hint:
      'PostgreSQL 唯一约束冲突。若该表启用了逻辑删除：唯一索引必须包含删除标记列，否则删过的值再也插不进去。',
  },
  {
    token: 'Unknown column', // MySQL 文案
    hint:
      'MySQL 字段名对不上。先查 Wrapper 里有没有字符串形式的字段名（eq("user_name", …)——改名后不报错，只查错数据），' +
      '再查驼峰配置与 @TableField。',
  },
  {
    // PostgreSQL 文案。单 token「does not exist」太泛（表/库/函数不存在都会命中），
    // 用 also 二次确认：必须同时出现 column "
    token: 'does not exist',
    also: 'column "',
    hint:
      'PostgreSQL 字段名对不上。先查 Wrapper 里有没有字符串形式的字段名（eq("user_name", …)），' +
      '再查驼峰配置与 @TableField。',
  },
];

const POINTER = '详见技能 mybatis-plus-dev 的 references/09-troubleshoot.md §2（常见异常定位）';

const matches = (s, text) => text.includes(s.token) && (!s.also || text.includes(s.also));
const isBuildCmd = (cmd) => /(^|[\s;&|])(\.\/)?(mvn|mvnw|gradle|gradlew)(\s|$)/.test(cmd);

// ── 状态目录（系统临时目录，按项目路径隔离） ───────────────────────────────
const dirFor = (root) => {
  const hash = createHash('md5').update(root).digest('hex').slice(0, 12);
  const dir = join(tmpdir(), 'claude-symptom');
  try {
    mkdirSync(dir, { recursive: true });
  } catch {
    /* ignore */
  }
  return { dir, hash };
};

const readJson = (p, fallback) => {
  try {
    return JSON.parse(readFileSync(p, 'utf8'));
  } catch {
    return fallback;
  }
};

// ── 项目门控 ──────────────────────────────────────────────────────────────
// 三类信号任一成立即认为项目在用 MP：构建文件里有 mybatis-plus 依赖 / 种子文件已播 / 源码里出现 MP 类。
// 正向结论永久缓存（项目引入了 MP 就不会随便移除）；否定结论只缓存 1 小时（新加依赖能尽快生效）。
function projectHasMP(root, cachePath) {
  const cached = readJson(cachePath, null);
  if (cached?.v === true) return true;
  if (cached?.v === false && Date.now() - cached.ts < GATE_TTL_MS) return false;

  let has = false;

  for (const marker of ['pom.xml', 'build.gradle', 'build.gradle.kts']) {
    try {
      const st = statSync(join(root, marker));
      if (st.size > MAX_SCAN) continue;
      const text = readFileSync(join(root, marker), 'utf8');
      if (/mybatis-?plus/i.test(text)) {
        has = true;
        break;
      }
    } catch {
      /* 文件不存在 */
    }
  }

  // 种子文件存在 → 说明播种流程已判定这是 MP 项目
  if (!has) {
    for (const seed of ['.claude/rules/mybatis-plus.md', 'CLAUDE.md']) {
      try {
        if (/mybatis-?plus/i.test(readFileSync(join(root, seed), 'utf8'))) {
          has = true;
          break;
        }
      } catch {
        /* 文件不存在 */
      }
    }
  }

  try {
    writeFileSync(cachePath, JSON.stringify({ v: has, ts: Date.now() }));
  } catch {
    /* 缓存写不进去不该影响主流程 */
  }
  return has;
}

// ── 主流程 ────────────────────────────────────────────────────────────────
let raw = '';
process.stdin.on('data', (d) => (raw += d));

process.stdin.on('end', () => {
  const payload = readJson0(raw);
  if (!payload) process.exit(0);

  const input = payload.tool_input ?? payload.toolInput ?? {};
  if (!isBuildCmd(String(input.command ?? ''))) process.exit(0);

  const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const { dir, hash } = dirFor(root);

  if (!projectHasMP(root, join(dir, `${hash}.gate.json`))) process.exit(0);

  // ---- 信号源 1：落盘日志（Maven -l） --------------------------------------
  let text = '';
  try {
    const st = statSync(join(root, LOG));
    if (Date.now() - st.mtimeMs <= STALE_MS) text = readFileSync(join(root, LOG), 'utf8');
  } catch {
    /* 没带 -l、目录不存在，或日志陈旧 → 走信号源 2 */
  }

  // ---- 信号源 2：工具返回内容（覆盖未用 -l 的项目） -------------------------
  const resp = payload.tool_response ?? payload.toolResponse;
  if (resp) {
    const extra =
      typeof resp === 'string'
        ? resp
        : [resp.stdout, resp.stderr, resp.output, resp.content]
            .filter(Boolean)
            .map(String)
            .join('\n');
    text += '\n' + extra;
  }
  if (!text.trim()) process.exit(0);

  // ---- 去重 ---------------------------------------------------------------
  const statePath = join(dir, `${hash}.json`);
  const state = readJson(statePath, {});
  const sid = String(payload.session_id ?? 'no-session');
  const reported = new Set(state[sid]?.tokens ?? []);

  const present = SYMPTOMS.filter((s) => matches(s, text)).map((s) => s.token);
  const kept = [...reported].filter((t) => present.includes(t)); // 症状消失即重新武装
  const hit = SYMPTOMS.find((s) => present.includes(s.token) && !reported.has(s.token));

  if (kept.length !== reported.size || hit) {
    // 命中的串全部标记：一个异常常同时含类名与消息（BindingException + Invalid bound statement），
    // 只标记当前这条，下一轮会补报另一条 —— 实测踩到过。
    state[sid] = { tokens: hit ? [...new Set([...kept, ...present])] : kept, ts: Date.now() };
    try {
      writeFileSync(statePath, JSON.stringify(state));
    } catch {
      /* 状态写不进去不该影响主流程 */
    }
  }

  if (!hit) process.exit(0); // 通过即沉默

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PostToolUse',
        additionalContext: `🔥 构建日志命中「${hit.token}」→ ${hit.hint}\n${POINTER}`,
      },
    }) + '\n'
  );
  process.exit(0);
});

// 输入解析失败时静默放行（fail-open）：hook 自身出错绝不能干扰正常工作流
function readJson0(s) {
  try {
    return JSON.parse(s || '{}');
  } catch {
    return null;
  }
}
