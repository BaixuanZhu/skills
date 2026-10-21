---
paths:
  - "**/*Mapper.java"
  - "**/*Mapper.xml"
  - "**/*ServiceImpl.java"
---
<!-- seeded: mybatis-plus-dev@3.0.0 -->

# MyBatis-Plus 项目约定

> 由 `mybatis-plus-dev` 播种，可整文件重新生成。`paths` 决定加载时机（只在读写 Mapper / XML / ServiceImpl 时注入），必须与项目实际文件名一致，写错是静默不加载。

## 事实

- 版本：MyBatis-Plus ⟨版本⟩ / SpringBoot ⟨版本⟩
- 数据库：⟨DbType⟩
- 分页 / 乐观锁 / 逻辑删除拦截器注册于：⟨配置类全限定名⟩
- Mapper 扫描：⟨@MapperScan("包路径")⟩；XML 位置：⟨mapper-locations⟩
- 逻辑删除字段：⟨字段名⟩，未删除值 ⟨值⟩，已删除值 ⟨值⟩
- 多数据源：⟨无 / @DS 注解，切换逻辑见 ⟨类名⟩⟩

## 流程（做完这一步才算完成）

- 新增 Mapper 方法 → 接口方法与 XML 的 `id` 必须同名同参；只写一边必然 `Invalid bound statement`
- 新增实体 → 显式写 `@TableName("表名")`，不靠驼峰推断（表名带前缀时会静默映射错）
- 改字段名 → 先 grep 旧名字符串，Wrapper 里可能有 `eq("user_name", …)` 这类漏网处：编译通过、运行查错数据

## 边界

- 联表 / 窗口函数 / 聚合 / 库专有函数 → 直接写 XML，不要在 Wrapper 里用 `apply` 拼
- 遇异常先看技能 `mybatis-plus-dev` 的 `references/09-troubleshoot.md` 与 `08-antipattern.md`
