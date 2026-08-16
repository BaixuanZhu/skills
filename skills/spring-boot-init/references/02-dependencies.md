# 02 · 初始依赖（按项目类型问询）

初始依赖由**项目类型**决定，类型不明**必问**——禁止默认堆一串依赖。

## 问询协议

1. 项目类型在 SKILL.md 问询轮的 C3 提出（第 0 步探测已得出类型也仍向用户确认）；答复含糊时追问一句（示例）：
   > "这是什么类型的服务？对外 Web API、带页面的全栈站点、定时任务 / 批处理，还是消息消费者？数据要落库吗（JPA 还是 MyBatis-Plus）？"
2. 按下表给**组合**推荐，向用户确认后再加；单项拿不准再单独问。
3. 用户说"先空骨架" → 只留模板自带的 web + test 基线（纯任务型服务可再去 web）。

## 项目类型 → 依赖组合

坐标全部不带 `<version>`（Boot 系由根 BOM、hutool 由根 hutool-bom 收敛，其余由根 dependencyManagement）。加到承载对应职责的模块：Web 类进可执行模块（sample-app），数据访问通常进业务模块。

| 项目类型 | 初始依赖（groupId 省略 `org.springframework.boot`） | 说明 |
|---|---|---|
| Web API（最常见） | `starter-web` + `starter-validation` + `starter-actuator` | 模板已含 web，补 validation + actuator |
| 服务端渲染全栈 | `starter-web` + `starter-thymeleaf` + `starter-validation` | |
| 定时任务 | `starter-quartz`（web 可选） | 无 HTTP 需求可去 web |
| 批处理 | `starter-batch`（web 可选） | |
| 消息消费 | `starter-amqp`（RabbitMQ）或 `org.springframework.kafka:spring-kafka` | 二选一 |
| 数据访问 · JPA | `starter-data-jpa` + `com.mysql:mysql-connector-j`（或 `org.postgresql:postgresql`） | 驱动同由 BOM 管版本 |
| 数据访问 · MyBatis-Plus | **不在本表** → mybatis-plus-dev | 本技能只搭骨架不含 ORM；初始化完成后由该技能接手引入 |
| 缓存 / 会话 | `starter-data-redis` + `starter-cache` | |
| 安全 | `starter-security`；国内更常用 Sa-Token → sa-token-dev | security 与 Sa-Token 二选一，勿叠加 |
| 通用工具库 | `cn.hutool:hutool-core` / `hutool-json` / `hutool-http` / `hutool-crypto` / `hutool-cache` 等按模块引；全量用 `hutool-all` | 根 hutool-bom 已纳管版本（hutool-all 由根直管），均无版本引用 |
| 测试 / 工具 | 模板已含 `starter-test` + lombok（根收敛） | 无需再加 |

写法示例（无版本）：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

## ✗ 禁止 → ✓ 推荐

| ✗ 禁止 | ✓ 推荐 |
|---|---|
| 类型不明就默认堆依赖（web + jpa + redis + security 全上） | 先问询定类型，按组合表加，确认后执行 |
| 凭记忆拼 starter ID（如不存在的 `spring-boot-starter-mybatis`） | 只用本表坐标；表外依赖先查 Maven Central 确认存在再加 |
| 子模块依赖带 `<version>` | 由根 BOM / dependencyManagement 收敛 |
| `starter-web` 与 `starter-webflux` 并存 | 二选一（Servlet 栈 vs Reactive 栈） |
