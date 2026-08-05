# 11 · SpringDoc / OpenAPI 3 接口文档

> SpringDoc（OpenAPI 3 规范实现）用法、注解、SpringBoot 2.x vs 3.x 依赖差异。**不含 Knife4j**（已停更，不推荐）。

## 一、为什么 SpringDoc（非 Swagger2 / Knife4j）

| 方案 | 规范 | 状态 |
|---|---|---|
| **SpringDoc** | OpenAPI 3 | **活跃维护，推荐** |
| springfox（Swagger2） | Swagger 2 / OpenAPI 3（后期） | **已停更**（2022 后无更新），3.x 兼容性差 |
| Knife4j | 基于 springfox / springdoc 的 UI 增强 | **已停更**（作者维护意愿低，社区转向 SpringDoc + 原生 UI） |

**结论**：SpringBoot 3.x 项目用 **`springdoc-openapi-starter-webmvc-ui`**；2.x 用 **`springdoc-openapi-ui`**。不引入 springfox / Knife4j。

## 二、依赖（按 SpringBoot 版本 + 是否需要 UI）

### SpringBoot 3.x（两个版本二选一）

```xml
<!-- 选项 A：带 Swagger UI（最常用，开发/测试环境） -->
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.6.0</version>
</dependency>

<!-- 选项 B：仅 JSON/YAML 接口（无 UI，生产环境 / 前端独立对接） -->
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-api</artifactId>
    <version>2.6.0</version>
</dependency>
```

| 坐标 | 含 UI | JSON/YAML 端点 | 适用场景 |
|---|---|---|---|
| `...-webmvc-ui` | ✓（Swagger UI） | ✓ | 开发/测试（默认选这个） |
| `...-webmvc-api` | ✗ | ✓ | 生产（不暴露 UI）/ 前端用第三方工具（如 Apifox）对接 |

> **命名陷阱**：3.x 用 `springdoc-openapi-starter-webmvc-*`（带 `starter-webmvc`），**不是** `springdoc-openapi-ui`（后者是 1.x 系，对应 2.x）。装错完全不工作。

### SpringBoot 2.x

```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-ui</artifactId>
    <version>1.7.0</version>                       <!-- 1.x 系（对应 SpringBoot 2.x），含 UI -->
</dependency>
<!-- 2.x 的纯 JSON 版本：springdoc-openapi-webmvc-core（1.x 系）-->
```

### 访问地址（默认）

- 文档 JSON：`http://localhost:8080/v3/api-docs`（`-ui` / `-api` 均提供）
- Swagger UI：`http://localhost:8080/swagger-ui/index.html`（仅 `-ui` 提供；SpringDoc 2.x）/ `swagger-ui.html`（1.x）

## 三、基础配置（`application.yml`）

```yaml
springdoc:
  api-docs:
    path: /v3/api-docs                              # JSON 端点路径（默认 /v3/api-docs）
    enabled: true
  swagger-ui:
    path: /swagger-ui.html                          # UI 路径
    enabled: true
    operationsSorter: method                        # 按 HTTP 方法排序
    tagsSorter: alpha                               # 按字母排序 tag
  packages-to-scan: com.app.controller             # 扫描包
  paths-to-match: /api/**                           # 只生成匹配路径的接口
```

## 四、注解（OpenAPI 3，非 Swagger2 老注解）

> **注解包**：`io.swagger.v3.oas.annotations.*`（OpenAPI 3）。**不要用** `io.swagger.annotations.*`（Swagger2 / springfox 老注解，与 SpringDoc 不配套）。

### 接口描述（Controller 方法）

```java
@RestController
@RequestMapping("/api/users")
@Tag(name = "用户管理", description = "用户的增删改查")       // 类级 tag
public class UserController {

    @Operation(summary = "查询用户详情")                       // 方法摘要
    @Parameter(name = "id", description = "用户 ID", example = "1", required = true)
    @GetMapping("/{id}")
    public Result<UserVO> getUser(@PathVariable Long id) { ... }
    // @ApiResponses 可选：声明多状态码；@RequestBody DTO 自动从 @Schema 读描述
}
```

### 模型描述（DTO / VO）

```java
@Schema(description = "用户创建请求")
public class UserCreateDTO {
    @Schema(description = "用户名", example = "alice", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank
    private String username;

    @Schema(description = "年龄", example = "25", minimum = "18", maximum = "120")
    @Min(18) @Max(120)
    private Integer age;
}
```

## 五、全局配置（`OpenAPI` Bean）

```java
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("用户服务 API")
                .version("1.0")
                .description("用户管理模块接口文档")
                .contact(new Contact().name("Team").email("team@example.com")))
            .addSecurityItem(new SecurityRequirement().addList("bearerAuth"))
            .components(new Components()
                .addSecuritySchemes("bearerAuth",
                    new SecurityScheme()
                        .type(SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")));
    }
}
```

> **JWT 鉴权配置**：上方配置后，Swagger UI 右上角出现「Authorize」按钮，输入 token 后所有请求自动带 `Authorization: Bearer <token>`。鉴权框架本身（Sa-Token）→ sa-token-dev，本技能只管 SpringDoc 文档如何配置。

## 六、分组（多模块 / 大项目）

```java
@Bean
public GroupedOpenApi userApi() {
    return GroupedOpenApi.builder()
        .group("user")
        .pathsToMatch("/api/users/**")
        .packagesToScan("com.app.controller.user")
        .build();
}

@Bean
public GroupedOpenApi orderApi() {
    return GroupedOpenApi.builder()
        .group("order")
        .pathsToMatch("/api/orders/**")
        .build();
}
```

访问 `http://localhost:8080/swagger-ui.html` 时可在下拉切换分组。

## 七、生产环境关闭文档

```yaml
# application-prod.yml
springdoc:
  api-docs:
    enabled: false                                  # 生产关闭（安全：不暴露接口结构）
  swagger-ui:
    enabled: false
```

> **生产建议关闭**：Swagger UI 暴露接口结构（参数 / 返回值），是信息泄漏风险。用 profile 控制（dev 开，prod 关）。

## 八、常见坑

### 坑 1：SpringDoc 版本与 SpringBoot 不匹配

| SpringBoot | SpringDoc | 结果 |
|---|---|---|
| 3.x | `springdoc-openapi-ui`（1.x） | **不工作**（1.x 不支持 3.x） |
| 3.x | `springdoc-openapi-starter-webmvc-ui`（2.x） | ✓ |
| 2.7.x | `springdoc-openapi-starter-webmvc-ui`（2.x） | **不工作**（2.x 不支持 2.7） |
| 2.7.x | `springdoc-openapi-ui`（1.x） | ✓ |

### 坑 2：用了 Swagger2 老注解

```java
// ✗ Swagger2 / springfox 老注解（io.swagger.annotations.*）
@Api(tags = "用户")                                // 应为 @Tag
@ApiOperation("查询用户")                          // 应为 @Operation
@ApiModel("用户创建")                              // 应为 @Schema
@ApiModelProperty("用户名")                        // 应为 @Schema

// ✓ OpenAPI 3 新注解（io.swagger.v3.oas.annotations.*）
@Tag(name = "用户")
@Operation(summary = "查询用户")
@Schema(description = "用户创建")
```

### 坑 3：文档不生成接口

- 检查 `springdoc.packages-to-scan` 是否包含 Controller 包。
- Controller 须有 `@RestController`（或 `@Controller` + `@ResponseBody`）。
- 方法须有 `@GetMapping` / `@PostMapping` 等映射注解。

### 坑 4：`@Parameter` 标在 `@PathVariable` 不生效

```java
// ✗ @Parameter 不直接驱动参数描述，@PathVariable 会被自动识别
@GetMapping("/{id}")
public Result get(@Parameter(description = "ID") @PathVariable Long id) { ... }

// ✓ 简单参数 @PathVariable / @RequestParam 自动识别，描述用类级 @Parameters 补充
@GetMapping("/{id}")
@Parameters({@Parameter(name = "id", description = "用户 ID", example = "1")})
public Result get(@PathVariable Long id) { ... }
```

## 九、最佳实践（仅列前文未详述项）

1. **DTO/VO 加 `@Schema`**——文档自动从注解生成，不手写说明。
2. **大项目按模块 `GroupedOpenApi`**——避免单页过载。

> 版本选择、Knife4j 规避、注解包、生产关文档、JWT 配置——见上文章节。

