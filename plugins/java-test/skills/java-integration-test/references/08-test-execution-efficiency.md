# 08 · 测试执行效率（token 与时间）

> Agent 跑集成测试有两个黑洞：**token 浪费**（全文读 Maven / Spring 输出）与**时间浪费**（反复全量跑、容器反复启停）。本文件固化执行效率护栏——测试不仅要写得对，还要跑得省。

## 反模式表（核心）

| ✗ 低效做法 | ✓ 高效做法 |
|---|---|
| 全文读取 `mvn test` 输出 | `-q` 降噪 + 定向 `grep` / `tail` |
| 反复全量 `mvn test` | 首次全量 → 之后 `-Dtest` 单测 / 单类 |
| 每次 `mvn clean test` | 只 `mvn test`（增量编译，不 clean） |
| 手动 `mvn spring-boot:run` 再测 | `@SpringBootTest` 进程内启动 |
| 失败后不看报告瞎改重跑 | 读 `target/surefire-reports/*.txt` 定位 |
| 测试无超时，死锁挂住套件 | `@Timeout` 兜底 |

## 1. Maven 输出降噪

```bash
# 只输出错误和测试摘要
mvn test -q

# 降级 Maven 自身日志
mvn test -q -Dorg.slf4j.simpleLogger.defaultLogLevel=warn

# 重定向 + 定向提取（推荐：保留全量日志供回溯，只回传关键行）
mvn test > target/test.log 2>&1
grep -E "Tests run:|BUILD|ERROR|FAIL" target/test.log
```

**原则**：执行测试后**不要全文回传 stdout**。要么 `-q` 降噪，要么重定向后只 `grep` / `tail` 关键行。失败详情看 surefire 报告，不看全量输出。

## 2. Spring 启动日志抑制

`@SpringBootTest` 启动 Spring 时打印的 Bean 注册、AutoConfiguration 条件评估、Hibernate SQL 是输出大头。靠 `application-test.yml` 压：

```yaml
logging:
  level:
    root: WARN
    org.springframework: WARN
    org.hibernate: ERROR
    org.mybatis: WARN          # 关掉开发期开的 SQL 日志
```

> 条件评估报告（CONDITIONS EVALUATION REPORT）只在 `--debug` 时才打印——跑测试别加 `--debug`。

## 3. 迭代策略：全量 → 单测 → 报告

```
首次：mvn test -q                                      # 验证整体
之后：mvn test -Dtest=OrderServiceTest                  # 只跑改动的类
      mvn test -Dtest=OrderServiceTest#should_create_order   # 只跑单个方法
失败：读 target/surefire-reports/*.txt 定位堆栈 → 修 → -Dtest 重跑
```

- `mvn clean` 触发全量重编译——日常迭代用 `mvn test`（增量），仅在有编译残留问题时才 `clean`。

## 4. 测试超时兜底

死锁 / 无限等待会挂住整个测试套件，且不报错。加超时兜底：

```java
@Test
@Timeout(10)                       // 默认单位秒
void should_not_hang() { ... }

@Timeout(30)                       // 类级
class SlowIntegrationTest { ... }
```

全局配置 `src/test/resources/junit-platform.properties`：

```properties
junit.jupiter.execution.timeout.default=30s
```

> 异步等待用 Awaitility 的 `atMost`（见 `06`），`@Timeout` 是套件级兜底——防止某测试死循环拖垮整个构建。

## 5. 集成测试不要盲目并行

JUnit 5 默认串行。集成测试并行执行有多个坑：Context 缓存失效（不同并行组合）、`@DirtiesContext`、Testcontainers 容器竞争、WireMock 固定端口冲突。**默认不开启并行**；确需提速先保证每个测试自包含（无共享状态、无固定端口），再考虑 `junit.jupiter.execution.parallel.enabled=true`。
