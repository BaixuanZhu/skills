# Backlog 规则（agile-backlog 参考）

## 一、ID 命名约定

| ID 前缀 | 含义 | 示例 |
|---------|------|------|
| `T-NNN` | 技术任务（Technical） | T-001 工程初始化 |
| `F-NNN` | 功能需求（Feature） | F-001 运营登录 |
| `B-NNN` | 缺陷修复（Bug） | B-001 支付重复回调重复发货 |

**不再使用** US（用户故事）/ EN（使能项）/ EPIC 命名——避免概念混淆。技术任务、功能需求与缺陷**平级**进入待办池。风险（R-NNN）/ 发布 / 决策（D-NNN）**不是条目**，各有真源文件，见 `risk-rules.md` / `release-rules.md` / `decision-rules.md`。

## 二、字段定义

每个条目是 `backlog.json` 里 `phases[].items[]` 的一个对象，字段如下：

| 字段 | 必填 | 说明 |
|------|------|------|
| id | ✅ | T-NNN / F-NNN / B-NNN，零填充 3 位，全局唯一 |
| title | ✅ | 一句话概括（动词 + 名词） |
| type | ✅ | 技术 / 功能 / 缺陷 |
| repo | — | 可选的单仓归属字符串（如 `api-server`）；跨仓业务条目省略，不能写数组/逗号串。实际接收方 repo 在工作包中 |
| points | ✅ | 整数。斐波那契（1/2/3/5/8/13，默认）；纯研究型 Sprint 可用线性（1/2/3/4/5），在 Sprint 文件头标注；过大无法估点 → 触发边界异常 ⑤（拆分） |
| priority | ✅ | Must / Should / Could / Won't |
| status | ✅ | 待办 / 已完成 / 已撤回 |
| refs | — | ADR 编号（如 `ADR-006`）或依赖条目 ID；无则省略 |
| basis | — | 点的来源（agent 推荐 / 用户确认）+ 优先级依据（开发顺序 / MoSCoW / 依赖 / ADR 优先级） |
| confirmed | ✅ | `true`（优先级/点数/验收已与用户确认）/ `false`（agent 推荐，Sprint 取用前必须显式转 true，见 §五） |
| created_at | 新条目 ✅ | 立项日期，ISO `YYYY-MM-DD`；存量条目无法确认时留空，不用文件修改时间或迁移日期冒充 |
| last_reviewed_at | — | 最近一次长期待办复核日期，ISO `YYYY-MM-DD`；仅在用户明确保留 / 调整后填写，不得早于 `created_at` |
| planned_sprints | — | 曾纳入的 Sprint 序号列表（如 `["001","003"]`），阶段 4 闭环同步时对 completed 与 moved_next 条目追加；Sprint 文件归档后「曾纳入」判定只剩这条戳记 |
| detail | — | 字符串数组，收 §四 判定「非显然」的展开内容；渲染成 bullets |
| delivery_acceptance | — | 工作包模式整体验收对象；仅脚本 `work finish` 写，阶段 4 保留，不由 agent 伪造或覆盖 |

`delivery_acceptance` 含 `project_id`、`sprint`、`revision`、`plan_digest`、`receipts`（回执 ID 数组）、`reviewer`、`evidence`（字符串数组）。它记录全部包验收后的整体业务验收，不是单包回执；协议以 `using-agile/references/sprint-schema.yaml` 的 `work_delivery` 为准。

一个业务需求可跨前后端，如 `F-001` 对应后端 `WP-001` 与前端 `WP-002`；不因仓库边界拆产品需求，`points` 仍属于整个条目，Sprint 只计一次，包不重复估点。

## 三、优先级排序逻辑

1. **开发顺序（用户指定）**：按用户口述的先后顺序（先做 A、再做 B）
2. **业务优先级（MoSCoW）**：Must > Should > Could > Won't
3. **依赖关系**：被依赖条目优先（如 T-001 工程初始化先于 T-002 引入 ArchUnit）。同一业务条目内部的跨仓实现依赖不拆成排序条目，工作包以 `depends_on` 指定具体交付包（`using-agile/references/workflow.md §三（工作包交付）`）；单执行者路径的跨仓交接仍用 `agile-sprint/references/sprint-template.md`「交接契约」段
4. **架构约束**：关联 ADR 的 T-NNN 按 ADR 优先级排

## 四、展开规则

判定"非显然"的客观标准（满足任一即需在底部"任务详情"区展开）：

- **验收标准非显然**：条目交付后用户/系统可观察的行为不能从标题直接推出
  - 示例："F-002 审核身份升级" → 展开"5 种身份申请单 / 营业执照校验 / 通过则附加身份到账号"
- **约束非显然**：条目受特定技术或业务约束
  - 示例："T-003 后台管理与用户端访问隔离" → 展开"两套登录态互不影响 / 管理端仅内网可达 / 关联 ADR-002"
- **关联非显然**：条目依赖其他条目或外部系统
  - 示例："T-010 Stripe 集成" → 展开"3DS / Webhook / 仅 SaaS 订阅场景"

判定"显然"（无需展开）：标题 + 点数 + 关联字段已完整表达意图。

**展开格式**：写进该条目的 `detail` 数组，3-5 条，覆盖验收 / 约束 / 关联即可。**禁止**写成完整用户故事格式（INVEST / Given-When-Then 仪式不要）。缺陷（B-NNN）展开「复现：{最短复现路径}」+「验收：修复后可观察行为」两行起。

### 范围 vs 实现（写入边界）

Backlog 定整个业务需求的**范围**（做什么），不是前后端各自的实现说明书。保留全项目 PRD/C4/ADR；工作包按接收方隔离实现上下文与具体交接依赖，消费 Agent 在本地代码上下文中拆子任务、记 checkbox，不写回全局 Backlog。

| 写 ✅（范围） | 不写 ❌（实现） |
|---------------|----------------|
| 可观察验收行为 | 技术方案 / 框架选型 |
| 业务与非功能约束 | 代码结构 / 类与方法设计 |
| 边界（做什么 / 不做什么） | SQL / 伪代码 / 具体 API 调用建议 |
| 依赖关联（条目 / ADR / 外部系统） | "建议做法"式实现细节 |

- 技术决策已在 ADR 拍板 → T-NNN 关联 ADR 章节即可，条目内不展开实现方案
- 反例（✗）：`"双 SecurityFilterChain 场景 → 展开 admin/app 两套分离 / 独立 SecurityFilterChain bean"` —— "独立 bean"即实现建议，应删，只留范围："两套访问控制互不影响"

## 五、状态流转与「可注记不可改写」

```
待办 ─────────────→ 已完成（整体条目验收；工作包须先全部包验收）
  │
  └─→ 已撤回（不参与排序 / 统计，留痕追溯）
```

**三态枚举**（`status` 字段）：`待办 / 已完成 / 已撤回`

- **待办**：默认状态，含已纳入 Sprint、工作包推进中或各包已验收但尚未整体业务验收。全局包协调状态在 delivery.json，本地子任务/checkbox 由消费 Agent 追踪，不扩充 Backlog 状态枚举
- **已完成**：整体条目验收通过。单执行者仍通过 DoD 后由阶段 4 同步；工作包须全部包验收后，再显式整体业务验收，由 `work finish` 原子写此状态与 `delivery_acceptance`，不等于 Sprint 已关闭
- **已撤回**：本阶段/本 Sprint 不再需要的条目，从池中摘出不参与排序与统计（全量统计时自动排除），仍留痕可追溯。撤回时追加「撤回时间 / 撤回原因 / 决策来源」，不改写条目原内容

**确认状态**（独立于 `status`，对应 `confirmed` 字段）：
- 「已确认」：优先级 / 点数 / 验收已与用户确认 → `true`
- 「agent 推荐待确认」：未与用户确认 → `false`，Sprint 取用前必须显式转 `true`（agile-sprint 跳过并告警）

Sprint 未完成条目在 `.done` 同步时 `moved_next → 待办`（不改优先级），**不设「移至下个Sprint」状态**。工作包模式必须消费 `work close` 生成的规范 `.done`；若 completed 缺整体验收，或 moved_next 含已整体验收条目，停止同步报冲突，禁止补造 `delivery_acceptance` 或把已整体验收状态降回待办。阶段 4 仍维护 `planned_sprints`、反馈与归档，不覆盖/删除验收记录。

### 长期待办复核（派生信号，不是第四态）

**长期未完成**：`status == 待办`、不属于任何活跃 Sprint、`created_at` 距今 ≥30 天。曾进入历史 Sprint 但目前仍是待办的条目也算，展示时区分「从未纳入 / 曾纳入 Sprint」（判定 = 条目出现在未归档 Sprint 文件的任务清单，或条目带 `planned_sprints` 戳记——Sprint 归档后只剩后者）；活跃 Sprint 条目由 Sprint 闭环负责，这里不重复提醒。

**待复核**：长期未完成条目中，`last_reviewed_at` 缺失或距今 ≥30 天。年龄始终从 `created_at` 计算，复核不会重置立项年龄；Could / Should / Must 同一口径，优先级不影响是否可见。

- `agile.py review` 展示全部长期未完成条目及待复核标记；创建时间未知或非法的待办单列，不参与年龄判定
- hook 只注入有界汇总，同项目同日最多展开提醒一次；年龄只是复核信号，**不是逾期、错误或撤回理由**
- 用户明确保留 / 调整 → 写入当天 `last_reviewed_at`；拆分出的条目继承原 `created_at`，原条目按用户裁决撤回并注明替代 ID；撤回 → 走本节现有撤回流程；只说「知道了」→ 不写复核日期
- ❌ 禁止因年龄自动改优先级、自动开 Sprint、自动撤回；✅ 由用户裁决后更新对应字段

### 已完成条目：「可注记、不可改写」

**已完成条目的事实不可变**（验收行为 / 关联 ADR / 当时决策内容）。后续需要修订时：

- ✅ **追加注记**：在条目下方追加 `> [YYYY-MM-DD] {变更摘要}。**已完成状态不变**。`——明确区分历史事实与后续决策；不篡改交付时快照
- ❌ **改写历史**：删旧验收 / 改点数 / 篡改关联——禁止（审计追溯的基础）
- 例外：用户明确裁决"撤回 / 废止已完成条目"→ 走本节撤回流程（状态 → 已撤回），历史事实仍不删，仅追加注记

惯例来源：评审类裁决影响已交付条目时（如 ADR 替代影响已完成条目的口径），追加注记而非改写历史（见 agile-strategic 门禁② 与 change-matrix.md §四 下游影响评估）。

## 六、门禁

详见 `using-agile/references/gate-protocol.md §二`（① 技术任务须关联 ADR）+ §三 边界异常 ⑤（过大条目拆分后估点）。

## 七、文件形态与命令（消费 Agent 读此文件）

`agile-docs/backlog.json` 是**唯一 Backlog 文件**（字段定义见 §二），由中枢 agile-backlog 维护；执行者不得直接写全局 Backlog/delivery。`delivery.json` 仅由插件脚本按需创建与维护，`delivery_acceptance` 只经 `work finish` 写入。人读概况 = 问 agent 或跑 `stats`；包协调状态用 `work status`。

> 5.6.0 起 PRODUCT-BACKLOG.md 渲染产物退役：不再生成、不再比对。遗留的 md 不再被维护或覆盖，确认无自定义内容后可删。

### 7.1 结构

```json
{
  "schema": 1,
  "phases": [
    {
      "id": 1,
      "title": "止血：下单链路可信",
      "items": [
        {
          "id": "T-001",
          "title": "下单入参与金额校验，错误响应不泄漏内部信息",
          "type": "技术",
          "repo": "order-service",
          "points": 3,
          "priority": "Must",
          "status": "待办",
          "refs": "ADR-007",
          "basis": "agent 推荐 / 缺陷止血",
          "confirmed": false,
          "created_at": "2026-11-02",
          "detail": ["验收：错误响应不含堆栈与 SQL", "约束：金额统一用分"]
        }
      ]
    }
  ]
}
```

两点与旧表格不同：`confirmed` 是布尔而不是 `✓ / 待确认`——机器侧本就该是布尔，符号只在渲染时出现；`detail` 是字符串数组，收 §四 判定「非显然」的展开内容。

### 7.2 命令

```bash
python <插件根>/scripts/agile.py stats   [项目根]   # 全量重算并打印，附长期未完成 / 待复核汇总
python <插件根>/scripts/agile.py review  [项目根]   # 只读列出长期未完成、Sprint 历史与复核状态
python <插件根>/scripts/agile.py check   [项目根]   # 结构校验 + 日期合法性 + Sprint 点数对账 + 回填内容校验 + Sprint 头状态词校验 + risks/releases/decisions 校验，有问题返回 1
python <插件根>/scripts/agile.py trend   [项目根]   # 已关闭 Sprint 趋势：承诺/完成点、完成率、顺延与反复顺延条目
python <插件根>/scripts/agile.py report  [项目根]   # 一页纸状态：战略/Backlog/风险/发布/决策/趋势
python <插件根>/scripts/agile.py brief   [项目根]   # 打印当前阶段与每轮基础注入原文（当日 review 展开提醒以 hook-prompt 为准）
```

`check` 的跨文件部分包括 `sprints/*.done.yaml` 的内容：引用了不存在的条目 ID、同一 ID 既在 `completed` 又在 `moved_next`、`feedback.type` 不是 `reason / issue / decision`、两个数组都空——这些在文件名层面看不出来，只能在内容层面报。

脚本在**插件的 `scripts/` 下，不在项目里**。装插件时其中两个动作已挂到 hook 上（写完 json 自动校验并对账、会话开始注入状态），通常不需要手动执行。

用 `npx skills` 只装技能文件时没有脚本也没有 hook：单执行者仍可按 §七.1 手写 Backlog、按 §七.3 全量算并沿用 `.done`；工作包模式必须先取得插件脚本，不手写 delivery 协议冒充同等自动化。

工作包命令与授权边界见 `using-agile/references/workflow.md §三（工作包交付）`、`agile-sprint/SKILL.md §3（工作包交付）`。`.done` 到达后，工作包模式须先跑 `python <plugin>/scripts/agile.py check HUB` 再过 DoD；completed 缺整体验收即拒绝闭环。`feedback.issue/decision` 随时回本技能，回执导入/汇总不能替代用户的产品裁决。

### 7.3 统计

统计由 `stats` 从 json 全量重算并打印。**不要手改统计数字，也不要自己写一段脚本去算**——已撤回条目不计入任何统计这条规则，脚本里已经写了（`status == "已撤回"` 的条目被排除）。长期未完成与待复核汇总也由脚本按 §五统一计算；条目级清单用 `review`，不要在状态快照里展开全部条目。

没有脚本可用时（无 python、非插件安装），按同一规则**覆盖式全量重算，禁止在旧数字上增量加减**；只有数字被改过而条目没动，就是漏算的信号。此时人工按 §五筛选长期待办，不得根据文件修改时间推测条目年龄。

### 7.4 旧格式转写（agent 一次性，脚本不再提供 migrate）

检测到 `backlog.json` 不存在、而 `PRODUCT-BACKLOG.md` 里还是「## 阶段 N」+ 表格 → 由 agent 按 §二 字段定义一次性转写成 `backlog.json`：表格每行一个条目（`—` 占位符写成空缺省字段），「任务详情」段并入对应条目的 `detail`，标题里的 `\|` 还原为字面 `|`。写完 hook 立即做结构校验 + Sprint 点数对账兜底。md 不会被生成或覆盖，原文件核对后由项目自行处置（可删）。

v4.x 的双文件（`PRODUCT-BACKLOG.yaml` / `.json`）同样处理：把其中仅机器侧持有的信息（adr_refs / confirmed / withdrawn）核对进新 json，删旧文件。旧格式没有 `created_at` 时，能从 Git 历史确认具体条目立项日期的才回填；无法确认的留空并进入 `review` 的「创建时间未知或非法」分组，**禁止统一写成迁移当天**。
