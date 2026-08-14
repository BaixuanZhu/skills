# 05 · REST Assured API 断言

> REST Assured 是 curl 的正式替代——用流式 DSL 写可断言、可重复、可版本控制的 API 测试。given/when/then 三段式语法自然表达请求构造 → 发送 → 断言。

## 依赖

```xml
<dependency>
    <groupId>io.rest-assured</groupId>
    <artifactId>rest-assured</artifactId>
    <version>6.0.1</version>
    <scope>test</scope>
</dependency>
```

> Spring Boot 项目 `spring-boot-starter-test` **不传递** REST Assured——需单独引入。
>
> 版本说明：6.x 需 Java 17+（核心 `rest-assured` 模块不依赖 Spring）。但 6.0 起 `spring-mock-mvc` 子模块 target Spring 7——Spring Boot 3.x（Spring 6）项目用 `RestAssuredMockMvc` 时选 5.5.x。

## RestAssured vs RestAssuredMockMvc

| | `RestAssured` | `RestAssuredMockMvc` |
|---|---|---|
| HTTP | 真实 HTTP（需 `RANDOM_PORT`） | MockMvc（进程内，无 HTTP socket） |
| 依赖 | `rest-assured` | `spring-mock-mvc`（`rest-assured` 的子模块） |
| 速度 | 十秒级（Context + HTTP） | 秒级（Context + Mock） |
| 适合 | 完整 HTTP API 测试 / E2E | Controller 层切片（替代 `@WebMvcTest` + 原生 MockMvc） |

```java
// RestAssured：真实 HTTP，需 RANDOM_PORT
@SpringBootTest(webEnvironment = RANDOM_PORT)
class ApiTest {
    @LocalServerPort int port;

    @BeforeEach void setup() {
        RestAssured.port = port;
    }
}

// RestAssuredMockMvc：走 MockMvc，不需 RANDOM_PORT
@SpringBootTest
@AutoConfigureMockMvc
class ControllerTest {
    @Autowired MockMvc mockMvc;

    @BeforeEach void setup() {
        RestAssuredMockMvc.mockMvc(mockMvc);
    }
}
```

> **不要混用**：`RestAssuredMockMvc` 走 MockMvc 管道（无真实 HTTP），`RestAssured` 走真实 HTTP。需要测试 HTTP 过滤器 / 序列化差异用 `RestAssured`；只测 Controller 逻辑用 `RestAssuredMockMvc` 或直接用 MockMvc。

## given/when/then 三段式

```java
@Test
void should_create_order_when_valid() {
    given()
        .contentType(ContentType.JSON)
        .header("Authorization", "Bearer " + token)
        .body(Map.of("productId", 1, "qty", 2))
    .when()
        .post("/api/orders")
    .then()
        .statusCode(200)
        .body("data.orderId", notNullValue())
        .body("data.status", equalTo("CREATED"))
        .body("data.totalAmount", equalTo(199.00f));
}
```

| 段 | 作用 | 典型方法 |
|---|---|---|
| `given()` | 请求构造 | `contentType`, `header`, `body`, `queryParam`, `pathParam`, `auth`, `cookie` |
| `when()` | 发送请求 | `get`, `post`, `put`, `delete`, `patch` |
| `then()` | 响应断言 | `statusCode`, `body`, `header`, `contentType`, `time` |

## 断言模式

### 状态码 + 响应体

```java
.then()
    .statusCode(201)
    .body("data.id", equalTo(1))
    .body("data.items.size()", equalTo(2))
    .body("data.items[0].name", equalTo("Widget"))
    .body("data.items.name", hasItems("Widget", "Gadget"));  // 提取所有 name
```

### jsonPath 断言

```java
.then()
    .body("data.orders.findAll { it.status == 'PAID' }.size()", equalTo(3))
    .body("data.orders.collect { it.total }.sum()", greaterThan(1000.0f));
```

### 提取值用于后续断言

```java
Integer orderId =
    given()
        .contentType(ContentType.JSON)
        .body(request)
    .when()
        .post("/api/orders")
    .then()
        .statusCode(201)
        .extract()
        .path("data.id");

// 用提取的 orderId 继续后续测试
given()
    .pathParam("id", orderId)
.when()
    .get("/api/orders/{id}")
.then()
    .statusCode(200);
```

### 响应时间断言

```java
.when()
    .get("/api/orders")
.then()
    .time(lessThan(2000L), TimeUnit.MILLISECONDS);  // P95 < 2s
```

## 认证

REST Assured 传递认证有两种方式：`auth()` DSL 和手动 header。选哪种取决于项目的认证机制——**先探测项目认证方式，再选对应写法**。

### 探测项目认证方式

| 线索 | 认证方式 | REST Assured 写法 |
|---|---|---|
| 请求头 `Authorization: Bearer xxx` | JWT / OAuth2 | `.auth().oauth2(token)` 或 `.header("Authorization", "Bearer " + token)` |
| 请求头 `Authorization: Basic xxx` | HTTP Basic | `.auth().basic(user, pass)` |
| 自定义 Header（`satoken` / `X-Token` / 等） | Sa-Token / 自定义 Token | `.header(tokenName, token)` — `tokenName` 从项目配置读取 |
| Cookie `JSESSIONID` | Session 认证 | `.cookie("JSESSIONID", sessionId)` |

> **不要假设认证方式**——探测项目的安全配置（`SecurityConfig` / Sa-Token 配置 / 拦截器注册）和登录接口的响应结构，选择对应写法。Sa-Token 的 token header 名由 `sa-token.token-name` 配置决定，不固定为 `Authorization`。

### auth() DSL

```java
// OAuth2 / Bearer Token
given()
    .auth().oauth2(token)
    .body(payload)
.when()
    .post("/api/orders")
.then().statusCode(200);

// HTTP Basic
given()
    .auth().basic("admin", "password")
.when()
    .get("/api/admin/users")
.then().statusCode(200);

// Preemptive Basic（先发凭证，不等 401 挑战）
given()
    .auth().preemptive().basic("admin", "password")
.when().get("/api/admin/users");
```

### 手动 Header（通用）

当项目使用自定义 Header 名（非标准 `Authorization`）时，用手动 header：

```java
// tokenHeader 从项目配置读取（如 sa-token.token-name → "satoken"）
String tokenHeader = "Authorization";  // 替换为项目实际 header 名

given()
    .header(tokenHeader, token)
    .body(payload)
.when()
    .post("/api/orders")
.then().statusCode(200);
```

### 获取 Token：先调登录接口

```java
// 通用模式：调登录接口 → 提取 token → 后续请求复用
// 登录端点路径、请求体结构、token 在响应中的字段路径——均跟随项目定义，不硬编码
String token =
    given()
        .contentType(ContentType.JSON)
        .body(loginRequest)       // 结构跟随项目登录接口
    .when()
        .post(loginEndpoint)      // 路径跟随项目定义
    .then()
        .statusCode(200)
        .extract()
        .path(tokenPath);         // token 在响应 JSON 中的路径，如 "data.token"
```

> 切片测试中模拟登录态（不走真实认证流程）的写法 → 见 reference 07「认证与权限测试」。

## 请求规格复用（RequestSpecification）

```java
RequestSpecification authSpec = new RequestSpecBuilder()
    .setContentType(ContentType.JSON)
    .addHeader("Authorization", "Bearer " + token)
    .setBaseUri("http://localhost")
    .build();

// 复用：每个测试只写差异部分
given()
    .spec(authSpec)
    .body(Map.of("productId", 1, "qty", 2))
.when()
    .post("/api/orders")
.then().statusCode(200);
```

> 多个测试共享相同的 header / contentType / 认证 → 抽成 `RequestSpecification`，减少重复。

## 文件上传

```java
given()
    .multiPart("file", new File("src/test/resources/test-data.csv"))
    .multiPart("description", "Monthly report")
.when()
    .post("/api/upload")
.then()
    .statusCode(200)
    .body("data.fileId", notNullValue());
```

## 日志

```java
given()
    .log().all()          // 打印请求（headers + body）
.when()
    .post("/api/orders")
.then()
    .log().ifError()      // 仅失败时打印响应
    .statusCode(200);

// 或全量打印
.then().log().all();
```

> 测试调试时用 `log().all()` 查看完整请求 / 响应。CI 中只开 `log().ifError()` 避免日志爆炸。

## curl vs REST Assured 对照

| 场景 | curl | REST Assured |
|---|---|---|
| 请求构造 | `-H "Content-Type: application/json" -d '{"name":"test"}'` | `.contentType(JSON).body(Map.of("name","test"))` |
| 状态码断言 | 无（肉眼看） | `.statusCode(200)` |
| 响应体断言 | 无（肉眼看） | `.body("data.id", equalTo(1))` |
| 可重复 | ✗（手动执行） | ✓（`mvn test` 自动跑） |
| CI 集成 | ✗ | ✓ |
| 版本控制 | ✗（终端历史） | ✓（代码仓库） |

## 多步串联模式（E2E 骨架）

REST Assured 的 `extract().path()` 让多接口串联变得自然——上一步的响应值传入下一步请求：

```java
// 模式：调接口 A → 提取 token → 构建 authSpec → 调接口 B → 提取 id → 调接口 C
String token =
    given().spec(spec)
        .body(loginRequest)
    .when()
        .post(loginEndpoint)          // 端点路径跟随项目定义
    .then().statusCode(200)
        .extract().path(tokenPath);   // token 在响应中的路径跟随项目定义

RequestSpecification authSpec = new RequestSpecBuilder()
    .addHeader(tokenHeader, token)    // header 名跟随项目认证方式（见上方「认证」）
    .setContentType(ContentType.JSON)
    .build();

Integer entityId =
    given().spec(authSpec)
        .body(createRequest)
    .when()
        .post(resourceEndpoint)
    .then().statusCode(201)
        .extract().path("data.id");   // 响应路径跟随项目响应结构

given().spec(authSpec)
    .pathParam("id", entityId)
.when()
    .get(resourceEndpoint + "/{id}")
.then().statusCode(200);
```

> 完整 E2E 业务流示例（含 Testcontainers、数据清理、多步断言、异常流程）→ **reference 07**。本节只展示 REST Assured 的串联语法。
