# 敏捷套件复评报告（v4.4.0 修复轮 · r2）

> **目的**：基线评估（`../darwin-validation-v4.4.0/`，均值 ≈81.0）后的修复轮复评。评分对象为当前工作区敏捷套件（版本号未变，含未提交修改 + 新增 `interview-protocol.md`）。
> **日期**：2026-08-15
> **方法**：复用基线 8 维度 rubric + 6 条 test-prompt；2 个独立盲评子 agent 双评 + 仲裁 agent 独立 grep 核实每条指控。
> **结论**：套件均值 **87.5/100**（基线 81.0，**+6.5**）。基线 5 项问题（1 P1 + 4 P2）全部已修复；本轮发现 **3 项新 P1 + 4 项 P2 + 10 项 P3**。

## 一、上一轮问题修复核验（全部通过）

| 基线问题 | 修复核验 |
|---|---|
| P1 DOD 模板多角色残留（至少 1 人 approve / PO 验收） | ✅ init-template.md:40-50 已改为 agent 自检 + 用户（唯一拍板人）验收 |
| P2 gate-protocol 异常表跳号（缺 ⑤） | ✅ §三现为 ①-⑥ 连续 |
| P2 vision-template 硬编码「终稿·不可逆」 | ✅ :19 已参数化为 `{终稿 · 不可逆 / 探索中}`，与决策点 3 一致 |
| P2 backlog 定位表漏阶段 4/5 | ✅ SKILL.md §1 表已含阶段 4（下游影响评估）/ 阶段 5（.done 同步） |
| P2 画像采集项在 DOD 模板无落盘列 | ✅ init-template.md:30-38 项目画像表 5 项齐全 |

## 二、评分结果（双评均值）

| 技能 | Agent A | Agent B | 均值 | vs 基线 |
|------|--------:|--------:|-----:|--------:|
| agile-sprint | 89.5 | 90.0 | **89.8** | +6.9 |
| agile-strategic | 88.5 | 88.5 | **88.5** | +6.1 |
| agile-backlog | 82.5 | 87.0 | **84.8** | +5.0 |
| using-agile | 89.0 | 84.5 | **86.8** | +7.8 |
| **套件均值** | 87.4 | 87.5 | **≈ 87.5** | **+6.5** |

> 两 agent 均值仅差 0.1。唯一明显分歧是 using-agile（A 89.0 / B 84.5）：B 发现了孤儿引用问题（下文 P1-1），A 的 D6=10 打分依据被仲裁 grep 推翻——`init-template.md` 在全套件 0 次被引用。B 的扣分更有证据支撑。

## 三、本轮发现的问题（仲裁已逐条 grep 核实）

### P1 实质缺陷（3 项）

1. **孤儿 reference：`init-template.md` 全套件零引用**（grep 证实）。`using-agile/SKILL.md:70` 要求「生成 DOD.md 模板」但全文无 `references/init-template.md` 指针——DOD 模板的全部实质内容（项目画像表 + 双层完成标准）只存在于 agent 读不到的文件里，初始化时会自拟结构。`sprint-schema.yaml` 半孤儿：SKILL.md:70 要求复制它但无源文件指针（仅 agile-sprint/sprint-template.md:82 有指针）。**修复**：SKILL.md §4 步骤 2/3 补两个指针。
2. **YAML 同步时机自相矛盾**（agile-backlog/SKILL.md）：`:112` 阶段 3「**在前两阶段确认后**生成/同步，避免提前出 YAML」vs `:129`「**每次写入/更新** .md 时同步生成/更新」vs `:164` 硬约束「**每次编辑 .md 后**必须同步更新 .yaml」。首次产出时阶段 1 写完排序表后三条指令互斥；且 md 有/yaml 无的中间态会触发 using-agile:55 双文件一致性检查误报。`:129`/`:164` 是分阶段改造前的旧规则残留，应限定为「YAML 已存在后的更新场景」。
3. **moved_next 状态映射矛盾 / 死枚举**：agile-backlog/SKILL.md:146 规定 .done 同步时 `moved_next → status:"待办"`（有理由：priority 不动、自然回顶部），但 backlog-rules.md:23/:58/:75 把「移至下个Sprint」定义为合法状态并收录 YAML schema 枚举——按 SKILL 路径该枚举永不被写入，消费 Agent 按 backlog-rules §七理解数据语义时与实际不符。**修复方向**：二选一——要么 backlog-rules 枚举删掉「移至下个Sprint」（该状态只存在于 Sprint 文件的「条目状态建议」），要么同步规则改为写入「移至下个Sprint」。

### P2 一致性瑕疵（4 项）

4. **门禁编号错位**：backlog-rules.md:21「过大无法估点 → 触发门禁 ⑥（拆分）」、:62「§二（…⑥ 过大条目拆分）」均错——gate-protocol §三 拆分实为 ⑤（⑥ 是 DoD 未定义却要关闭），且 §二 业务门禁只有 ①-④；agile-backlog SKILL.md:171 自己写的是正确的「边界异常 ⑤」。
5. **多人团队残留**：strategy-conflict-template.md:4「请用户/产品负责人裁决」、:45「最终由产品负责人裁决」——与 SKILL.md:24 单人+agent 哲学、init-template.md:45「用户（唯一拍板人）」口径冲突（同类问题上轮 P1 的漏网之鱼）。
6. **双文件一致性检查口径不一**：using-agile SKILL.md:55 查「id 集合 + status」，agile-backlog SKILL.md:51 查「id/priority/status」，backlog-rules §七 查「id 集合 + 条目数 + priority/status」。同一检查三处粒度不同。
7. **估点/优先级来源标注无落地字段**：agile-backlog SKILL.md:90 要求「估点标来源 / 优先级判断标依据」，但排序表 schema（SKILL.md:83-87 七列 + backlog-rules §二字段表）无对应列，agent 只能自行发明放法。

### P3 可选优化（10 项）

8. 「候选 + 推荐 + 你来说」问询口径跨文件重复 7+ 处（agile-strategic SKILL.md 内 4 处）；L1/L2/L3 分级被 3 个业务技能复述——可收敛为纯指针。
9. 硬约束节大面积重述正文（agile-backlog §5 12 条中约 8 条逐字重述 §2/§3；agile-strategic §5 同样）——双份维护是 #6 口径不一的根源。
10. probing-protocol.md:47「本节取代 gate-protocol §四 旧话术」为过时维护注记（gate-protocol:61 已是指针），可删。
11. agile-strategic SKILL.md:145 下游影响评估只挂在 L3 行，L2 行未提（:147 段落可兜底）。
12. agile-backlog SKILL.md:85 vs :123 同文件示例不一致（md 示例 T-001 关联 ADR-001/005，yaml 示例同 id 写 adr_refs ADR-003）。
13. backlog-rules.md:50-54 状态流转 ASCII 图回流箭头指向含糊。
14. sprint-rules.md:10（0.7-0.75）与 agile-sprint SKILL.md:44 选项 C（0.7）口径未统一。
15. backlog-rules.md:28「阶段 0 → 阶段 1」指代含糊（易误读为产出阶段 0-5，实指用户口述开发顺序）。
16. 「五条规则（详见 interview-protocol）」后各技能列出的条数不一致（strategic 列 4 条、backlog 列 3 条）。
17. sprint-template.md:25 规划期预写「执行结果: ….done.yaml（由消费 Agent 生成）」，消费 Agent 读到可能误以为文件已存在。

### 仲裁误报澄清

- Agent A 对 using-agile 的 D6=10（「references 全部被正确指针引用」）不成立：grep 证实 init-template.md 零引用（见 P1-1）。取 B 的 D6=6 为准。
- 其余指控经 grep 全部核实为真，无其他误报。

## 四、D8 干跑结论（两 agent 一致）

6 条 test-prompt 全部可产出合格结果、不卡住：T1 初始化、T2 愿景、T3 backlog、T4 Sprint、T5 变更分级、T6 ADR 选型的验证点（选择题问询 / 来源标注 / 分阶段即停 / 回填要求内置 / L1-L2-L3 / ADR 4 行依据）全部命中。残留漂移风险：T1 的 DOD 模板内容不可达（P1-1）、T3 的 YAML 同步时机矛盾（P1-2）。

## 五、结论与建议

- 修复轮成效明确：基线 5 项问题全修复，均值 81.0 → 87.5。
- 本轮 3 项 P1 集中在 **agile-backlog（2 项）与 using-agile 初始化指针（1 项）**，均为小改动可修：补 2 个指针、限定 2 条旧同步规则的适用范围、消解 moved_next 枚举二选一。
- P2 的 4 项（编号错位 / 产品负责人 / 口径不一 / 标注无落地）建议与 P1 同批修复，属同一类「旧规则残留」。

## 六、产物清单

- `blind-A.md` / `blind-B.md` — 两份独立盲评报告
- `report.md` — 本报告（含仲裁核实结论）

复现：`bash` 见基线 `../darwin-validation-v4.4.0/report.md §六`，评分对象换成当前工作区。
