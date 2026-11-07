# 决策日志规则（agile-backlog 参考）

`agile-docs/decisions.json` 是决策记录唯一真源。**文件不存在 = 尚无需要留痕的裁决，不建空文件**。跨技能流转全貌见 `using-agile/references/workflow.md`，本文件只定义字段与口径。

## 一、结构与字段

```json
{
  "schema": 1,
  "decisions": [
    {
      "id": "D-001",
      "decision": "首版不做分销",
      "outcome": "不做",
      "basis": "用户裁决：MVP 聚焦核心链路",
      "date": "2026-11-07",
      "refs": ["F-002"]
    }
  ]
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| id | ✅ | D-NNN，零填充 3 位，全局唯一 |
| decision | ✅ | 裁决内容一句话 |
| outcome | ✅ | 做 / 不做 |
| basis | ✅ | 依据 + 裁决来源（用户裁决 / agent 推荐，用户授权） |
| date | ✅ | 裁决日期，ISO `YYYY-MM-DD` |
| refs | — | 关联条目 ID（T-/F-/B-）或 ADR 编号 |

## 二、何时记

| 来源 | 时机 |
|------|------|
| feedback.decision 裁决 | agile-backlog 阶段 4 处理反馈时，裁决完即记；outcome=做 再转条目 |
| L3 变更裁决 | change-matrix L3 走完完整问询、用户拍板后记 |
| 用户主动 | 说「记录决策」时 |

**「明确忽略」= outcome 不做，必须留痕**——忽略即丢是审计断点。

## 三、口径

- 只记裁决结果，不记讨论过程（讨论素材归条目 `detail` 或 ADR）
- 已记的决策不改写；推翻旧决策 → 新记一条，`basis` 注明「替代 D-NNN」（同 ADR 替代思路）
- agent 推荐未经用户确认的不记（推荐 ≠ 裁决）；用户说「你看着办」按 probing-protocol 标 agent 推荐后执行的，记 basis「agent 推荐，用户授权」

## 四、命令

结构校验随 `agile.py check`；最近裁决进 `agile.py report` 一页纸。
