# 战略冲突待裁决模板（using-agile 参考）

> 本模板由 `using-agile` 或 `agile-strategic` 在「写前战略门禁」触发时生成。
> 写完即停，请用户裁决。

## 一、何时生成

「写前战略门禁」触发时生成（触发条件、生成方优先级与去重规则见 `references/gate-protocol.md §一`，本文件不重复）。

## 二、文件路径

```
{project-root}/agile-docs/STRATEGY_CONFLICT.md
```

> 与 VISION.md / ARCHITECTURE.md 同级。

## 三、模板正文

```markdown
# 战略冲突待裁决

> 生成时间：{ISO 8601}
> 生成方：{using-agile / agile-strategic}
> 状态：待裁决

## 一、冲突清单

| # | 维度 | 选项 A | 选项 B | 影响面 |
|---|------|--------|--------|--------|
| 1 | 部署模式 | SaaS 多租户 | 私有化部署 | 架构边界重画；新增 ADR（隔离方案）；3 个新 T-NNN |
| 2 | 计费形态 | 按调用量计费 | 一次性买断 | 商业化模块重写；KPI 体系重设 |

## 二、建议（非决定）

- 冲突 1：建议 ____（引用现有 VISION/ADR 的具体段落为理由）
- 冲突 2：建议 ____

> ⚠️ 建议仅供参考，最终由用户裁决。

## 三、裁决记录（用户填写）

- 冲突 1 裁决：____（A / B / 其他）
- 冲突 2 裁决：____

## 四、后续动作

裁决后：
1. 由对应业务技能（agile-strategic / agile-backlog / agile-sprint）吸收裁决结论
2. 删除本文件
```
