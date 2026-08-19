# 04 · Testcontainers 真实依赖

> 用 Docker 容器启动真实依赖（PostgreSQL / MySQL / Redis / Kafka），消除"H2 测试 + PostgreSQL 生产"的环境差异。Testcontainers 是集成测试用真实依赖的事实标准。示例基于 TC 1.x（Boot ≤3.x，BOM 3.5 管 1.21.x）；Boot 4 用 TC 2.x——坐标 / 包名 / 泛型差异见「依赖」节对照表。

## 为什么不用 H2

| 差异 | H2 | PostgreSQL |
|---|---|---|
| `jsonb` 类型 | ✗ 不支持 | ✓ |
| `ARRAY` 类型 | ✗ | ✓ |
| `SERIAL` / `GENERATED ... AS IDENTITY` | 语义部分不同 | ✓ |
| 大小写敏感 | 默认不敏感 | 敏感（需引号） |
| 窗口函数 / CTE | 部分支持 | 完整支持 |
| 存储过程 / 函数 | 语法不同 | ✓ |

> H2 与 PostgreSQL 的方言差异是"测试绿生产炸"的头号来源。H2 测试通过的 SQL，在 PostgreSQL 上可能直接报语法错误或行为不同。Testcontainers 用真实数据库消除这个差异。

## 基本用法

### 依赖

```xml
<!-- spring-boot-testcontainers：@ServiceConnection + 传递依赖 testcontainers 核心（版本由 Spring Boot BOM 管理，不手写） -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-testcontainers</artifactId>
    <scope>test</scope>
</dependency>
<!-- 二选一按 Boot 版本；数据库模块 + JUnit 扩展需显式引入，版本仍由 BOM 管理 -->

<!-- Boot ≤3.x（TC 1.x）：旧名无前缀 -->
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>postgresql</artifactId>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>junit-jupiter</artifactId>
    <scope>test</scope>
</dependency>

<!-- Boot 4（TC 2.x）：模块全部加 testcontainers- 前缀，旧名在 2.x 下不存在（404） -->
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>testcontainers-postgresql</artifactId>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>testcontainers-junit-jupiter</artifactId>
    <scope>test</scope>
</dependency>
```

> 版本由 Spring Boot BOM 管理，**不手写 `<version>`、不显式引 `testcontainers` 核心**（`spring-boot-testcontainers` 已传递）。Boot 3.5 BOM 管 1.21.3——Docker v29（2026）需 ≥1.21.4（1.x 线末版），用 `<testcontainers.version>1.21.4</testcontainers.version>` 属性 override，勿逐模块硬编码；Boot 4 BOM 管 2.0.x，无此问题。

**TC 1.x → 2.x 差异（Boot 3 → 4 迁移必读）**：

| | TC 1.x（Boot ≤3.x） | TC 2.x（Boot 4） |
|---|---|---|
| 模块名 | `postgresql` / `junit-jupiter` / `mysql` … | 加前缀：`testcontainers-postgresql` / `testcontainers-junit-jupiter` …（旧名 2.x 下 404） |
| 容器类 import | `org.testcontainers.containers.PostgreSQLContainer` | `org.testcontainers.postgresql.PostgreSQLContainer`（每模块独立包） |
| JUnit 4 | 支持（`@Rule`） | 移除（仅 Jupiter） |

```java
// TC 2.x（Boot 4）写法对照：import 换包、容器类无泛型，其余不变
import org.testcontainers.postgresql.PostgreSQLContainer;

@Container
static PostgreSQLContainer postgres = new PostgreSQLContainer("postgres:16-alpine");
```

> `@Testcontainers` / `@Container` / `@ServiceConnection` / `withReuse` 等 API 模式两版一致——差异集中在坐标、import 包名、泛型（2.x 容器类不再带 `<>`）三处。核心 artifact `org.testcontainers:testcontainers` 名字不变（Redis 用的 `GenericContainer` 不受影响）。

### @Container + static：全类共享

```java
@SpringBootTest
@Testcontainers
class PostgresIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:16-alpine");

    // 容器全类共享——只启动一次，所有测试方法共用
}
```

> **`@Container` + `static`**：容器在类加载时启动、类卸载时停止——所有测试方法共享同一个容器实例。不写 `static` 则每个测试方法启停一次（十秒级 × N），极慢。

### @ServiceConnection（Spring Boot 3.1+）

```java
@SpringBootTest
@Testcontainers
class PostgresTest {

    @Container
    static PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:16-alpine")
            .withReuse(true);  // 跨测试类复用容器

    @ServiceConnection  // 自动注入 datasource.url / username / password
    // 替代 @DynamicPropertySource——一行搞定
}
```

`@ServiceConnection` 让 Spring Boot 自动从容器中读取连接信息，不需要手写 `@DynamicPropertySource`。支持 PostgreSQL / MySQL / Redis / MongoDB / Kafka / LocalStack 等主流容器。

### @DynamicPropertySource（3.0 及以下）

```java
@Container
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

@DynamicPropertySource
static void configure(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
}
```

> Spring Boot 3.1+ 优先用 `@ServiceConnection`（更简洁）；3.0 及以下用 `@DynamicPropertySource`。

## @DataJpaTest + Testcontainers

```java
@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class OrderRepositoryIT {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired OrderRepository orderRepository;

    @Test
    void should_query_by_jsonb_field() {
        // 这条 SQL 用了 jsonb 操作符 ->>，H2 根本不支持
        orderRepository.save(createOrderWithJsonb("{\"category\":\"electronics\"}"));

        List<Order> result = orderRepository.findByCategory("electronics");

        assertThat(result).hasSize(1);
    }
}
```

> `@AutoConfigureTestDatabase(replace = NONE)` 必须——否则 `@DataJpaTest` 默认用 H2 替换，Testcontainers 容器白启动。

## 容器复用

```java
@Container
static PostgreSQLContainer<?> postgres =
    new PostgreSQLContainer<>("postgres:16-alpine")
        .withReuse(true);  // 标记可复用
```

```properties
# application-test.properties 或 testcontainers.properties
testcontainers.reuse.enable=true
```

复用模式下，容器在**第一次测试启动后不停止**——后续测试类直接复用已运行的容器。开发时本地反复跑测试，省掉每次十秒启动。

> 复用只对 `withReuse(true)` 且全局开启 `testcontainers.reuse.enable=true` 生效。CI 中通常关闭复用（每次干净环境）。

## 常用容器速查

| 依赖 | 容器类 | Maven artifactId |
|---|---|---|
| PostgreSQL | `PostgreSQLContainer` | `org.testcontainers:postgresql` |
| MySQL | `MySQLContainer` | `org.testcontainers:mysql` |
| Redis | `GenericContainer("redis:7-alpine")` | `org.testcontainers:testcontainers` |
| MongoDB | `MongoDBContainer` | `org.testcontainers:mongodb` |
| Kafka | `KafkaContainer` | `org.testcontainers:kafka` |
| LocalStack (AWS) | `LocalStackContainer` | `org.testcontainers:localstack` |
| Elasticsearch | `ElasticsearchContainer` | `org.testcontainers:elasticsearch` |

> 上表 artifactId 为 TC 1.x（Boot ≤3.x）名；Boot 4（TC 2.x）除核心 `testcontainers` 外全部加 `testcontainers-` 前缀（如 `testcontainers-mysql`、`testcontainers-kafka`），容器类 import 同步换独立包（见「依赖」节对照表）。

### Redis 示例

```java
@Container
@ServiceConnection
static GenericContainer<?> redis =
    new GenericContainer<>("redis:7-alpine").withExposedPorts(6379);
```

> `@ServiceConnection` 对 Redis 的支持（Spring Boot 3.1+）自动注入 `spring.data.redis.host` / `port`。3.0 及以下手动 `@DynamicPropertySource`。

## Flyway / Liquibase 迁移测试

### 为什么必须用真实库测迁移

容器启动后，Flyway / Liquibase 正常执行迁移脚本——与生产行为一致。**这是 H2 做不到的**：

| DDL 语法 | H2 | PostgreSQL |
|---|---|---|
| `CREATE TYPE ... AS ENUM` | ✗ 语法不支持 | ✓ |
| `CREATE INDEX ... CONCURRENTLY` | ✗ | ✓ |
| `ALTER TABLE ... ADD COLUMN ... DEFAULT ...` | 语义部分不同 | ✓ |
| `CREATE EXTENSION` (pgcrypto等) | ✗ | ✓ |
| `ALTER TYPE ... ADD VALUE`（枚举扩展） | ✗ | ✓ |

> 迁移脚本在 H2 上全绿，部署到 PostgreSQL 上 `CREATE TYPE order_status AS ENUM` 直接报错——这是"测试绿生产炸"的典型场景。

### Flyway：默认即迁移测试

```java
@Container
@ServiceConnection
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

// application-test.yml 中正常配置（与生产一致）
// spring.flyway.enabled: true （默认 true，不需要额外配置）
// spring.flyway.locations: classpath:db/migration
```

> **只要 Testcontainers 启动了真实 PostgreSQL，Flyway 迁移脚本自动执行**——集成测试本身就是在验证迁移脚本能否在真实库上跑通。不需要额外注解。

### Flyway clean + migrate：验证迁移可重放

```java
@Test
void should_migrations_run_cleanly_on_fresh_database() {
    // Flyway.clean() 清空所有表和结构 → 模拟全新环境
    // Flyway.migrate() 从头执行所有迁移脚本
    // 如果任何脚本有语法错误或顺序依赖问题 → 测试失败
    flyway.clean();
    assertThat(flyway.migrate().getSuccessfulMigrations()).isNotEmpty();
}
```

> `clean` + `migrate` 验证的是"迁移脚本能否在空库上从零跑通"。这能抓到：脚本顺序依赖错误、遗留的已应用脚本被修改（Flyway checksum 校验失败）、DDL 语法不兼容。

### Liquibase 等价方案

```java
@Autowired SpringLiquibase liquibase;

@Test
void should_changelog_run_cleanly() throws Exception {
    liquibase.setDropFirst(true);  // 先清空再执行
    liquibase.afterPropertiesSet(); // 重新执行 changelog
    // changelog 中任何 changeset 语法错误 → 抛异常 → 测试失败
}
```

> Liquibase 的 `dropFirst=true` 等价于 Flyway 的 `clean()`。两者目的相同：验证迁移可重放。

### 迁移测试不是单独的测试类型

集成测试已隐式验证迁移脚本（容器启动时 Flyway/Liquibase 执行，脚本有问题则容器初始化阶段就炸）——单独写测试只在验证**可重放**（clean + migrate）时才有意义。

## Docker 要求

Testcontainers 依赖 Docker daemon：
- **本地开发**：装 Docker Desktop（Windows/macOS）或 Docker Engine（Linux）。
- **CI 环境**：GitHub Actions / GitLab CI 预装 Docker；自建 Jenkins 需配 Docker-in-Docker 或远程 Docker。

> **CI 无 Docker 的降级方案**：如果 CI 环境无法跑 Docker，可退回 H2 + 接受方言差异风险，但须在团队内明确标注"集成测试覆盖不完整"。这不应是默认状态。

## 隐蔽坑

### ① 容器不写 static → 每个测试方法启停

```java
// ✗ 不写 static：每个 @Test 启动 + 停止容器
@Container
PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");
// 10 个测试方法 = 启停 10 次容器 = 数分钟

// ✓ static：全类共享一次
@Container
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");
```

### ② 镜像首次拉取慢

首次使用 `postgres:16-alpine` 会拉镜像（~150MB），耗时数十秒。后续从本地 Docker 缓存启动（秒级）。CI 中可预拉镜像加速。

### ③ @ServiceConnection 需要 spring-boot-testcontainers 依赖

漏引 `spring-boot-testcontainers` → `@ServiceConnection` 不生效，容器启动但连接信息不注入。Maven 不报错（注解存在），但测试时数据源连接不上。
