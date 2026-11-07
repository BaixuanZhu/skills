# 发布记录规则（agile-backlog 参考）

`agile-docs/releases.json` 是发布记录唯一真源。**文件不存在 = 尚无发布规划，不建空文件**。跨技能流转全貌见 `using-agile/references/workflow.md`，本文件只定义字段与流转。

## 一、结构与字段

```json
{
  "schema": 1,
  "releases": [
    {
      "id": "v1.0",
      "title": "首个可用版本",
      "items": ["F-001", "T-003"],
      "status": "规划中",
      "checks": { "rollback": true, "migration": false, "notice": false },
      "released_at": "2026-12-01"
    }
  ]
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| id | ✅ | 版本号即 ID（如 `v1.0`），全局唯一 |
| title | ✅ | 一句话版本目标 |
| items | ✅ | 构成条目的 ID 列表（T-/F-/B-，须存在于 `backlog.json`） |
| status | ✅ | 规划中 / 已发布 / 已取消 |
| checks | ✅ | 固定三键布尔，语义见 §三 |
| released_at | 已发布时 ✅ | 规划中 = 计划发布日（可为未来）；已发布 = 实际发布日期（不得晚于当天） |

## 二、流转

```
规划中 ──→ 已发布（checks 过 + released_at）
   └────→ 已取消（不删记录，原因注明在 title 或 basis）
```

- 状态变更由**用户裁决**，agent 不自动标已发布
- items 可增删直到发布；已发布的 items 不改写（与已完成条目「可注记不可改写」同口径）
- Sprint 关闭时的「完成条目并入哪个 release」提示只是入口之一，用户可随时组版本

## 三、检查单（checks 三键）

| 键 | 含义 |
|----|------|
| rollback | 回滚方案已确认（出问题怎么退回来） |
| migration | 数据迁移已确认（含「无迁移可做」——确认了也算过） |
| notice | 相关人已通知（含「无需通知」） |

`agile.py check` 对「已发布但 checks 有 false」给提示、**不阻断**——检查单防漏事，不做门禁。

## 四、命令

结构校验随 `agile.py check`；发布清单与统计随 `agile.py stats` / `report`。
