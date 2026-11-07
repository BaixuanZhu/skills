# 风险台账规则（agile-backlog 参考）

`agile-docs/risks.json` 是风险唯一真源。**文件不存在 = 本项目未启用风险管理，不建空文件**。跨技能流转全貌见 `using-agile/references/workflow.md`，本文件只定义字段与生命周期。

## 一、结构与字段

```json
{
  "schema": 1,
  "risks": [
    {
      "id": "R-001",
      "title": "第三方地图配额不足导致打卡失败",
      "status": "活跃",
      "impact": "核心流程不可用",
      "response": "提前申请配额，超限降级缓存",
      "hit_ref": "T-014",
      "basis": "用户给出",
      "created_at": "2026-11-07"
    }
  ]
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| id | ✅ | R-NNN，零填充 3 位，全局唯一 |
| title | ✅ | 一句话风险描述 |
| status | ✅ | 活跃 / 已发生 / 已解除 / 已接受 |
| impact | ✅ | 一句话后果（语义描述，不打分） |
| response | — | 应对措施一句话 |
| hit_ref | — | 已发生时转出的条目 ID（T-/F-/B-）；status=已发生 后必填 |
| basis | — | 来源标注（用户给出 / agent 推断） |
| created_at | ✅ | 登记日期，ISO `YYYY-MM-DD` |

## 二、生命周期

```
识别 → 活跃 ──→ 已发生（转条目 + hit_ref）
        ├────→ 已解除（应对成功或风险消失）
        └────→ 已接受（不应对，影响可承受）
```

- **无概率矩阵、无 severity、无自动升级**——排序交给 Sprint 规划时人工看 impact 语义 + 用户裁决
- 不设复核日期：Sprint 规划「过一遍活跃风险」就是复核时机
- 已发生后不删条目：风险留痕，hit_ref 指向转出的条目

## 三、识别与转条目

识别入口见 `using-agile/references/workflow.md §一` 信号表。**登记须经用户确认，agent 不静默建风险。**

转条目（status → 已发生时）：

1. 在 `backlog.json` 建对应条目（按内容判 T-/F-/B-）
2. 风险 `status` 改「已发生」、`hit_ref` 填新条目 ID
3. 条目 `basis` 注明「来源：风险 R-NNN」

## 四、命令

结构校验随 `agile.py check`；统计行随 `agile.py stats`；状态注入显示活跃数。写后由 hook 校验结构（错则阻断）、跨文件引用（提示不阻断）。
