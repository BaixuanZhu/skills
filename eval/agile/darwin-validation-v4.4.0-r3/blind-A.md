# 敏捷套件 v4.4.0 修复轮复评（盲评 Agent A）

> 评分对象：r2 修复后的当前工作区。rubric 复用 `../darwin-validation-v4.4.0/rubric.md`。
> 注：本报告由盲评子 agent 原样归档，其"套件均值 86.1"为算术错误（四技能分 89.5/89.0/87.5/88.2 的均值应为 88.6），仲裁已在 report.md 更正；分技能分数不受影响。

## 一、分技能打分表

### using-agile（SKILL.md + 8 references）

| 维度 | 权重 | 分 | 理由（文件:行号） | 加权 |
|---|---|---|---|---|
| D1 | 8 | 9 | frontmatter 齐全，description 含触发词+不适用边界（SKILL.md:6） | 72 |
| D2 | 15 | 9 | 激活/初始化/变更三流程均有编号步骤与明确输入输出（SKILL.md:48-101） | 135 |
| D3 | 10 | 8 | 双文件不一致停报、.done.yaml 双态处理、>1 活跃 Sprint 警告均覆盖；但残留 STRATEGY_CONFLICT.md 不在检测清单（status-routing.md:9-20） | 80 |
| D4 | 7 | 9 | 逐层询问不替用户决定走向、裁决前不写任何产物；唯 §3.3「自动路由」措辞与「逐层询问」有轻微张力（:57） | 63 |
| D5 | 15 | 9 | 检测清单、路由决策表、变更分级判定表均可机械执行 | 135 |
| D6 | 5 | 10 | SKILL.md 引用的 8 个 references 全部存在且指针编号正确（§4→init-template §二/probing §三均实存） | 50 |
| D7 | 15 | 9 | 入口「只检测路由不写业务文档」定位贯彻；§5 与 gate-protocol §一为摘要+指针关系，无实质重复 | 135 |
| D8 | 25 | 9 | T1/T5 干跑均能正确落点 | 225 |

**总分：89.5**

### agile-strategic（SKILL.md + 2 references）

| 维度 | 权重 | 分 | 理由 | 加权 |
|---|---|---|---|---|
| D1 | 8 | 9 | description 触发词密度高且含路由来源条件 | 72 |
| D2 | 15 | 9 | 阶段 0/A/B 表 + 选型裁决四步，每步输入输出明确 | 135 |
| D3 | 10 | 8 | 跳层兜底、约束矛盾质疑路径、「你看着办」降级路径覆盖好；缺「VISION 已存在但用户只要架构」的显式分支 | 80 |
| D4 | 7 | 9 | 阶段 A 写完即停硬约束、用户坚持时如实记录不越权 | 63 |
| D5 | 15 | 10 | §2.1 八项决策点逐项给候选方向+追问触发+兜底，§3.1 必答话题表带提问示例——全套件最佳 | 150 |
| D6 | 5 | 9 | 本技能 2 个 references 存在；跨技能指针经 agile group 插件可达 | 45 |
| D7 | 15 | 8 | §2.0 的 4 条要点与 interview-protocol.md 近乎逐条重复；vision-template.md:1-3 残留「815 融合版」维护者元信息 | 120 |
| D8 | 25 | 9 | T2/T6 干跑均能正确落点 | 225 |

**总分：89.0**

### agile-backlog（SKILL.md + 1 reference）

| 维度 | 权重 | 分 | 理由 | 加权 |
|---|---|---|---|---|
| D1 | 8 | 9 | 触发词+前置条件写明 | 72 |
| D2 | 15 | 9 | 阶段 0-5 表 + 每阶段「写完停」节点，阶段 3 YAML 同步时机规则明确（:112,129） | 135 |
| D3 | 10 | 8 | 跳层前置、双文件不一致停报、过大条目拆分、变更分级覆盖好；阶段 5 同步前未要求先做一致性校验 | 80 |
| D4 | 7 | 9 | 估点「接受/调整」选项而非静默采纳、每阶段结构化审阅 | 63 |
| D5 | 15 | 9 | 字段表、状态枚举两态、YAML 契约均具体；唯 .md「关联」列多 ADR 写法无规范（"ADR-001/005"） | 135 |
| D6 | 5 | 9 | references 指针全部可达 | 45 |
| D7 | 15 | 8 | 分阶段+双文件设计自洽；backlog-rules 示例残留 yudao/ArchUnit/Stripe 历史项目痕迹 | 120 |
| D8 | 25 | 9 | T3 干跑能正确落点 | 225 |

**总分：87.5**

### agile-sprint（SKILL.md + 2 references）

| 维度 | 权重 | 分 | 理由 | 加权 |
|---|---|---|---|---|
| D1 | 8 | 9 | 触发词+yaml 非空前置 | 72 |
| D2 | 15 | 9 | 环节 A/B/C 顺序清晰，序号/日期命名规则具体 | 135 |
| D3 | 10 | 8 | .done 缺失→人工确认、临时清单拒绝路径覆盖好；.done.yaml 含非法 ID 时无显式处理 | 80 |
| D4 | 7 | 10 | 容量三参数必问、明文「禁止静默按 0.6 默认」、每环节即停——检查点设计为套件最强 | 70 |
| D5 | 15 | 9 | 容量公式+系数档位、闭环检查纯列表具体可执行 | 135 |
| D6 | 5 | 9 | 2 个 references 存在，交叉引用编号正确 | 45 |
| D7 | 15 | 8 | sprint-rules「线性估点」授权与 backlog-rules「点=斐波那契」单一点数所有权冲突；「放回 Backlog 顶部」与「不直接修改 PRODUCT-BACKLOG」措辞矛盾；sprint-template 文件头无「估点体系」字段位 | 120 |
| D8 | 25 | 9 | T4 干跑能正确落点 | 225 |

**总分：88.2**

## 二、问题清单

**P1：无。** r2 修复重点区域（using-agile §4 初始化指针、backlog YAML 同步时机与状态枚举、backlog-rules 门禁编号与状态流转、双文件一致性口径、strategy-conflict 角色措辞）逐一核对，均已修复且相互一致。

**P2：**
1. sprint-rules.md:30-33 「纯研究型 Sprint 允许线性估点」与 backlog-rules.md:21（点=斐波那契，字段层硬性定义）冲突；点数所有权在 backlog，sprint 不产点，此条无落地钩子。
2. sprint-rules.md:13 「超额则放回 Backlog 顶部」暗示 sprint 可调整 Backlog 排序，与 agile-sprint SKILL.md:81「不直接修改 PRODUCT-BACKLOG」矛盾（实义应为「不取用」）。
3. status-routing.md:9-20 检测清单不含 STRATEGY_CONFLICT.md——冲突文件生成后若用户未裁决再次激活入口，待裁决状态不出现在状态表/路由决策中。
4. sprint-template.md:17-25 文件头无「估点体系」字段占位，sprint-rules.md:33 要求「必须在 Sprint 文件头标注估点体系：线性」时无处落笔（与问题 1 同源）。

**P3：**
1. agile-strategic SKILL.md:44-48 §2.0 四条要点与 interview-protocol.md 近乎逐条重复；gate-protocol.md:59 第三次复述。
2. vision-template.md:1-3 「815 融合版」维护者溯源元信息；红线类别示例带特定 B2B 项目味道。
3. backlog-rules.md:7-8,31,39,43 yudao/ArchUnit/Stripe 等历史项目示例；gate-protocol.md:37「yudao RBAC 映射」同源。
4. using-agile SKILL.md:57 「自动路由」与「逐层询问」措辞张力。
5. agile-backlog SKILL.md:85 「关联」列多 ADR 的 .md 写法无字段规范。
6. using-agile SKILL.md:55 双文件不一致确认「以哪份为准」后由谁修复另一份未指明。
7. agile-backlog SKILL.md:142-149 阶段 5 同步前可先跑 §2a 一致性校验。
8. strategy-conflict-template.md:14 vs 52-57 生成方/吸收方链路半开放（backlog/sprint 未提生成/吸收义务）。

## 四、D8 干跑

6/6 通过（T1 初始化 / T2 愿景 / T3 backlog / T4 Sprint / T5 变更 / T6 ADR），无跑偏或卡死路径；扣分集中在 P2 边角场景（研究型 Sprint、超额放回措辞）可能诱导错误微行为，主线不受影响。
