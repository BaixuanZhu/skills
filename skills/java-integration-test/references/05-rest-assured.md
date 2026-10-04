# 05 · REST Assured（版本事实与选型）

> REST Assured 是 curl 的正式替代——流式 DSL 写可断言、可重复、可版本控制的 API 测试（given/when/then 语法 agent 均熟，本文只留版本事实与选型判据）。属本技能（重型测试，激活后）工具；开发期本地接口测试也常用它连 `RANDOM_PORT`（→ java-unit-test `03`）。

## 依赖与版本分流（事实——易错处）

```xml
<!-- Boot 4：BOM 已不管理 rest-assured，必须手写 version（6.0.1 为当前最新） -->
<dependency>
    <groupId>io.rest-assured</groupId>
    <artifactId>rest-assured</artifactId>
    <version>6.0.1</version>
    <scope>test</scope>
</dependency>
```

- Spring Boot 项目 `spring-boot-starter-test` **不传递** REST Assured——需单独引入。
- **Boot ≤3.x 的 BOM 管理 rest-assured（3.5 管 5.5.x）——删掉 `<version>` 走 BOM**；且用 `RestAssuredMockMvc`（`spring-mock-mvc` 子模块）时**必须停在 5.5.x**——6.0 起该子模块 target Spring 7，Boot 3.x（Spring 6）项目用 6.x 不兼容。
- Boot 4 手写 `6.0.1`（6.x 需 Java 17+，核心 `rest-assured` 模块不依赖 Spring）。

## RestAssured vs RestAssuredMockMvc

| | `RestAssured` | `RestAssuredMockMvc` |
|---|---|---|
| HTTP | 真实 HTTP（需 `RANDOM_PORT`） | MockMvc（进程内，无 HTTP socket） |
| 依赖 | `rest-assured` | `spring-mock-mvc`（`rest-assured` 的子模块） |
| 速度 | 十秒级（Context + HTTP） | 秒级（Context + Mock） |
| 适合 | 完整 HTTP API 测试 / E2E | Controller 层切片（替代 `@WebMvcTest` + 原生 MockMvc） |

> **不要混用**：需要测试 HTTP 过滤器 / 序列化差异用 `RestAssured`；只测 Controller 逻辑用 `RestAssuredMockMvc` 或直接 MockMvc。端口用 `@LocalServerPort` 注入 + `RestAssured.port = port`，不写死。

## 认证：先探测项目方式，不假设

| 线索 | 认证方式 | 写法 |
|---|---|---|
| 请求头 `Authorization: Bearer xxx` | JWT / OAuth2 | `.auth().oauth2(token)` 或 `.header("Authorization", "Bearer " + token)` |
| 请求头 `Authorization: Basic xxx` | HTTP Basic | `.auth().basic(user, pass)` |
| 自定义 Header（`satoken` / `X-Token` 等） | Sa-Token / 自定义 Token | `.header(tokenName, token)`——token 名从项目配置读（Sa-Token 由 `sa-token.token-name` 决定，不固定为 `Authorization`） |
| Cookie `JSESSIONID` | Session 认证 | `.cookie("JSESSIONID", sessionId)` |

> 探测项目的安全配置（`SecurityConfig` / Sa-Token 配置 / 拦截器）和登录接口响应结构再选写法。多步拿 token：`given().post(loginEndpoint).then().extract().path(tokenPath)`——端点 / 请求体 / token 路径跟随项目定义，不硬编码。

## 多步串联（E2E 骨架）

`extract().path()` 让串联自然——上一步响应值传入下一步：

```java
String token = given().spec(spec).body(loginRequest)
    .when().post(loginEndpoint).then().statusCode(200)
    .extract().path(tokenPath);                      // 跟随项目定义

RequestSpecification authSpec = new RequestSpecBuilder()
    .addHeader(tokenHeader, token).setContentType(ContentType.JSON).build();

Integer id = given().spec(authSpec).body(createRequest)
    .when().post(resourceEndpoint).then().statusCode(201)
    .extract().path("data.id");
```

> 共享 header / contentType → 抽 `RequestSpecification` 复用。调试用 `log().all()`，CI 只开 `log().ifError()`。完整 E2E 业务流示例（含容器、清理、多步断言）→ `07`。
