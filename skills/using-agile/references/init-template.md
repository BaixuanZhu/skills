# 初始化模板（using-agile 参考）

## 一、目录骨架（空目录树，不含业务内容）

```
project-root/
├── agile-docs/                    # 战略 + 执行层文档
│   ├── VISION.md                  # [战略层] 由 agile-strategic 阶段 A 产出
│   ├── ARCHITECTURE.md            # [战略层] 由 agile-strategic 阶段 B 产出（C4 合并）
│   ├── ADR.md                     # [战略层] 由 agile-strategic 阶段 B 产出（章节式）
│   ├── PRODUCT-BACKLOG.md         # [执行层] 由 agile-backlog 产出（人读）
│   ├── PRODUCT-BACKLOG.yaml       # [执行层] 由 agile-backlog 产出（Agent 轻量读取）
│   ├── DOD.md                     # [执行层] 完成定义（本技能生成模板）
│   └── interfaces/
│       └── sprint-schema.yaml     # Sprint 接口契约（本技能初始化时生成）
└── sprints/                       # 短周期工作区（与 agile-docs 平级，初始为空）
```

> 注：以上仅描述 `agile-docs/` 的**最终结构**，初始化时**只建目录 + DOD.md + interfaces/sprint-schema.yaml**，不创建任何业务文档占位文件（VISION/ARCHITECTURE/ADR/PRODUCT-BACKLOG.* 由对应业务技能在用户确认后产出）。占位文件会让"文件存在性路由"误判状态已就绪。

路由决策以文件存在性为准，不依赖中心化状态文件。

## 二、DOD.md 模板（完成的定义，占位待确认）

```markdown
# 完成的定义 (DoD)

> 本模板由 using-agile 生成，请逐条确认 / 增删。DoD 是 Sprint 的**独立出口门禁**，关闭 Sprint 前必须逐条验证。

## 项目画像（初始化采集，下游技能探询的公共输入）

| 项 | 值 |
|----|----|
| 项目类型 | {Web 应用 / API 服务 / 工具库… 或 {待确认}} |
| 团队人数与技能栈 | {如 3 人，Java/Vue 或 {待确认}} |
| 代码基础 | {全新 / 存量（简述） 或 {待确认}} |

## 任务完成标准（每个 T-/F- 条目关闭前须全部满足）
- [ ] 代码已提交并通过 CI（构建 + 单元测试）
- [ ] 功能通过验收标准（若条目展开了验收）
- [ ] 已完成代码评审（至少 1 人 approve）
- [ ] 相关文档 / API 说明已更新
- [ ] 产品负责人（PO）已验收

## Sprint 完成标准（关闭 Sprint 前须全部满足）
- [ ] 所有承诺任务满足上述「任务完成标准」
- [ ] 无遗留未解决项
- [ ] 可发布增量已在 Sprint 文件标注（若本 Sprint 含可发布增量）
```
