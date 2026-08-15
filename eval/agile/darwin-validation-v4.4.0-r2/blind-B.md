# 敏捷套件 v4.4.0 独立 rubric 评分（Agent B）

> 盲评子 agent 独立产出，评分对象为当前工作区（基线评估后的修复轮，版本号未变）。rubric 复用 `../darwin-validation-v4.4.0/rubric.md`。所有 17 个文件已通读，关键指控均经 grep 复核。

---

## 1. 分技能打分表

### using-agile（SKILL.md + 8 references）

| 维度 | 分 | 加权 | 理由（证据） |
|---|---|---|---|
| D1 | 9 | 7.2 | frontmatter 完整，description 为触发词+排除项长文本（符合仓库约定） |
| D2 | 9 | 13.5 | 激活 6 步、初始化 5 步、变更协调 8 步，每步输入输出明确 |
| D3 | 9 | 9.0 | 双文件不一致停下报告、.done.yaml 双态检测、>1 活跃 Sprint 警告、6 类异常场景 |
| D4 | 9 | 6.3 | 逐层询问不替用户决定、变更先列后改须确认、裁决前禁写 |
| D5 | 8 | 12.0 | 初始化第 3 步「生成 DOD.md 模板」（:70）未指明模板来源文件 |
| D6 | 6 | 3.0 | **`init-template.md` 与 `sprint-schema.yaml` 是孤儿 reference**：SKILL.md 全文对二者 0 次引用（grep 证实） |
| D7 | 9 | 13.5 | 入口-路由-变更三职责清晰，references 单一职责 + 指针交叉引用为主 |
| D8 | 8 | 20.0 | T1 能跑通但 DOD 模板内容不可达；T5 协调链完整 |
| **总分** | | **84.5** | |

### agile-strategic（SKILL.md + 2 references）

| 维度 | 分 | 加权 | 理由 |
|---|---|---|---|
| D1 | 9 | 7.2 | description 触发词密集，dependencies 合规 |
| D2 | 9 | 13.5 | 三阶段表 + 每阶段「前置问询→产出→写完即停」结构一致 |
| D3 | 9 | 9.0 | 跳层兜底、前置条件回退表、变更分级、STRATEGY_CONFLICT 触发优先 |
| D4 | 9 | 6.3 | 矛盾选型必须质疑、「你看着办」有处理路径、每项裁决后才写 ADR |
| D5 | 9 | 13.5 | 八行决策点表 + 七行必答话题表，可直接执行 |
| D6 | 9 | 4.5 | 所有引用文件均存在，跨技能引用路径可达 |
| D7 | 8 | 12.0 | §5 硬约束 8 条几乎逐条重述 §2/§3；「选择题+推荐+你来说」口径本文件出现 4 次 |
| D8 | 9 | 22.5 | T2/T6 完整命中验证点 |
| **总分** | | **88.5** | |

### agile-backlog（SKILL.md + 1 reference）

| 维度 | 分 | 加权 | 理由 |
|---|---|---|---|
| D1 | 9 | 7.2 | description 含触发词+前置条件，双 dependencies 合规 |
| D2 | 9 | 13.5 | 六阶段表每阶段有前置与产出物，阶段 1-3 模板内嵌 |
| D3 | 9 | 9.0 | 跳层门禁拦截、双文件三字段校验、.done 同步仅改 status 不动 priority |
| D4 | 9 | 6.3 | Must 范围挑战、估点须确认、验收「不许自行脑补」 |
| D5 | 9 | 13.5 | 阶段 3 YAML 示例与 backlog-rules §七 schema 完全一致 |
| D6 | 9 | 4.5 | backlog-rules.md 多处正确引用 |
| D7 | 7 | 10.5 | **moved_next→「待办」（:146）与 backlog-rules:23,58,75「移至下个Sprint」枚举冲突**（P1）；§5 硬约束 12 条大量重述 |
| D8 | 9 | 22.5 | T3 分阶段+估点选择题+ADR 关联全部命中 |
| **总分** | | **87.0** | |

### agile-sprint（SKILL.md + 2 references）

| 维度 | 分 | 加权 | 理由 |
|---|---|---|---|
| D1 | 9 | 7.2 | description 含触发条件 |
| D2 | 9 | 13.5 | 环节 A/B/C 各有输入输出与停点，sprint-template 指针去重 |
| D3 | 9 | 9.0 | .done 缺失→人工确认、口头清单不能进 Sprint、gate ③ 拦截 |
| D4 | 9 | 6.3 | 容量三参数禁止静默默认、Sprint 目标反问、关闭前须问 |
| D5 | 9 | 13.5 | 容量公式+系数选项、序号扫描规则、点数回读 .md 因 yaml 无 point |
| D6 | 9 | 4.5 | sprint-template.md:82 明确 schema 源在 using-agile/references/ |
| D7 | 9 | 13.5 | 最小最聚焦，模板五段与 sprint-schema 逐段对应 |
| D8 | 9 | 22.5 | T4 全部命中验证点 |
| **总分** | | **90.0** | |

## 2. 总分

| 技能 | 总分 |
|---|---|
| using-agile | 84.5 |
| agile-strategic | 88.5 |
| agile-backlog | 87.0 |
| agile-sprint | 90.0 |
| **套件均值** | **87.5** |

## 3. 问题清单

### P1
1. **孤儿 reference：`init-template.md` 与 `sprint-schema.yaml` 不可达** — SKILL.md:69-70 要求产出二者但零引用（grep 证实）。DOD 模板全部实质内容只存在于未被指向的文件中，agent 会自拟 DOD 结构；schema 复制动作不会被触发。
2. **moved_next 状态映射矛盾** — SKILL.md:146 规定同步时 `moved_next → "待办"`，backlog-rules:23/:58/:75 把「移至下个Sprint」定义为合法状态并收录 schema 枚举。该枚举值永不被写入 yaml，成为死值。

### P2
3. **多人团队残留** — strategy-conflict-template.md:4,45「产品负责人」与单人+agent 口径冲突。
4. **双文件一致性检查口径不一** — using-agile SKILL.md:55 只查「id 集合和 status」，agile-backlog SKILL.md:51 与 backlog-rules.md:80-85 查三字段。
5. **过时的「取代」注记** — probing-protocol.md:47。
6. **下游影响评估的级别归属歧义** — agile-strategic SKILL.md:145 仅 L3 行列下游影响评估，L2 行未提（:147 段落可部分兜底）。

### P3
7. 「选择题+候选+推荐+你来说」口径跨文件重复 7+ 处。
8. 硬约束节大面积重述正文（agile-backlog §5 12 条中约 8 条重述）。
9. 接口版本无对齐机制（sprint-schema "1.3" vs PRODUCT-BACKLOG "1.0"）。
10. 边界异常 ① 粒度不一致（gate-protocol「建目录骨架再继续」vs 前置表「→ using-agile 初始化」含画像采集）。

## 4. D8 干跑结论

T1 基本合格（DOD 模板内容不可达留小漂移）；T2 合格；T3 合格；T4 完全合格；T5 合格留一处歧义；T6 完全合格。宣称能力在 6 条干跑中全部可执行且不卡住。
