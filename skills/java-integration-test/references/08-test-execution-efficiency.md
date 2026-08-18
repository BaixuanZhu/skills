# 08 · 测试执行效率（token 与时间）

> Agent 跑集成测试有两个黑洞：**token 浪费**（全文读 Maven / Spring 输出）与**时间浪费**（反复全量跑、容器反复启停）。本文件固化执行效率护栏——测试不仅要写得对，还要跑得省。

## 反模式表（核心）

| ✗ 低效做法 | ✓ 高效做法 |
|---|---|
| 全文读取 `mvn test` 输出 | `-B -ntp` + `-q` 分层降噪 + 定向 `grep` / `tail`（§1） |
| 反复全量 `mvn test` | 首次全量 → 之后 `-Dtest` 单测 / 单类 |
| 每次 `mvn clean test` | 只 `mvn test`（增量编译，不 clean） |
| 手动 `mvn spring-boot:run` 再测 | `@SpringBootTest` 进程内启动 |
| 失败后不看报告瞎改重跑 | 读 `target/surefire-reports/*.txt` 定位 |
| 测试无超时，死锁挂住套件 | `@Timeout` 兜底 |

## 1. Maven 输出降噪

`mvn test` 控制台噪声分两层，参数各对口。**`-q` 只管 Maven 自己的日志**——被测应用直写 stdout 的 Spring 日志、测试的 System.out 都不受它影响（分别见 §2 / 下文落盘）。

**① 依赖下载噪声** → `-B`（批处理模式，关交互式渲染，任何版本）+ `-ntp`（`--no-transfer-progress`，Maven ≥ 3.6.1，压掉 Downloading/Downloaded 传输行与进度显示；`-B` 单用不压传输行）：

```bash
mvn test -B -ntp
```

**② Maven 自身 INFO 日志** → `-q` 或降 logger 级别。两者都压掉全部 Maven INFO——**含成功时的 "Tests run" 摘要**（失败时摘要以 `[ERROR]` 打出，仍可见）：

```bash
mvn test -q                                              # 只留 ERROR
mvn test -Dorg.slf4j.simpleLogger.defaultLogLevel=warn   # 多保留 WARN 级
```

要保留 Tests run 摘要就别压 Maven INFO——用 `-B -ntp` + 下文重定向提取。

**持久化：`.mvn/maven.config`（Maven ≥ 3.3.1）**——Maven 层参数写进仓库，agent / 开发者 / CI 的每次 `mvn` 自动生效：

```
# <项目根>/.mvn/maven.config —— 一行一个参数（3.9+ 强制：一行多参报 "Unable to parse maven.config file options"；3.3.1~3.8 按空白拆分。单参单行全版本安全）
-B
-ntp
-Dorg.slf4j.simpleLogger.defaultLogLevel=warn
```

只放 Maven 层参数：`-q` 不进（对所有调用静默，要全量输出排查时 CLI 无参数调回）；应用层参数（`logging.level.*`）也不进（会波及 `spring-boot:run` 等一切 Maven 驱动的运行）——应用层归 §2。

**测试自身 stdout 多（System.out / printStackTrace）** → `-q` 管不到（fork JVM 直写），让 surefire 落盘（pom.xml）：

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-surefire-plugin</artifactId>
  <configuration>
    <redirectTestOutputToFile>true</redirectTestOutputToFile>
  </configuration>
</plugin>
```

stdout 落 `target/surefire-reports/<TestClass>-output.txt`，控制台不再出现。

**重定向 + 定向提取**（推荐：保留全量日志供回溯，只回传关键行）：

```bash
mvn test -B > target/test.log 2>&1
grep -E "Tests run:|BUILD|ERROR|FAIL" target/test.log
```

**原则**：执行测试后**不要全文回传 stdout**。要么 `-q` 降噪，要么重定向后只 `grep` / `tail` 关键行。失败详情看 surefire 报告，不看全量输出。

## 2. Spring 启动日志抑制

`@SpringBootTest` 启动 Spring 时打印的 Bean 注册、AutoConfiguration 条件评估、Hibernate SQL 是输出大头——**直写 stdout，`-q` 压不到**（§1）。两道闸：

**持久（推荐）**：`src/test/resources/application-test.yml`——只影响测试，不波及开发运行：

```yaml
logging:
  level:
    root: WARN
    org.springframework: WARN
    org.hibernate: ERROR
    org.mybatis: WARN          # 关掉开发期开的 SQL 日志
```

**临时（命令行，免改文件）**：surefire 会把 Maven 进程系统属性传入测试 JVM，Spring Boot 从系统属性读 `logging.level.*`（优先级高于 yml）：

```bash
mvn test -Dlogging.level.root=WARN -Dspring.main.banner-mode=off
```

banner 不走日志（`logging.level` 压不掉），须单独 `spring.main.banner-mode=off`。最早期 1~2 行 spring-test 框架 INFO（`Found @SpringBootConfiguration` 等）在 Spring Boot 接管日志前打出，压不掉——无害残余，别为它加配置。

> 两套 `-D` 别混：`org.slf4j.simpleLogger.*` 管 **Maven 自身**日志（§1 ②）；`logging.level.*` 管**被测 Spring 应用**日志（本节），且仅在项目用 Spring Boot 默认日志（Logback）时生效——指定了 `logging.config` / `logback.configurationFile` 则不生效。

**全链路一键**（下载 + Maven 日志 + Spring 日志三层全压，实测 109 行 → 8 行）：

```bash
mvn test -B -ntp -q -Dlogging.level.root=WARN -Dspring.main.banner-mode=off
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
