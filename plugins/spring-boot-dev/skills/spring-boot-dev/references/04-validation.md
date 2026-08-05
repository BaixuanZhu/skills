# 04 · 参数校验：`@Validated` vs `@Valid` + 分组校验

> Bean 校验（JSR303 / Jakarta Validation）在 Spring Boot 里的用法、分组校验失效坑、参数绑定差异、自定义校验器。校验不触发是最高频坑。

## 一、前置：依赖

```xml
<!-- SpringBoot 2.x -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

- 命名空间：SpringBoot 2.x / 3.x 均用 `spring-boot-starter-validation`（坐标一致），但内部 `javax.validation`（2.x）vs `jakarta.validation`（3.x）。
- **`spring-boot-starter-web` 不传递校验依赖**（2.4 起已拆分，2.x / 3.x 均须显式引入 `-validation`）。漏引则所有校验注解静默失效。

## 二、`@Valid` vs `@Validated`（决策表）

| 维度 | `@Valid` | `@Validated` |
|---|---|---|
| 来源 | JSR303 标准（`jakarta.validation.Valid`） | Spring（`org.springframework.validation.annotation.Validated`） |
| 分组 | ✗（校验全部约束） | ✓（指定 groups） |
| 标注位置 | **参数前**（`@Valid UserDTO`） / 嵌套属性 | **类前** 或 **参数前** |
| 方法级校验（非 Bean 参数） | ✗ | ✓（类级 `@Validated` 触发方法参数校验） |

**核心规则**：
- **Bean 参数**（`@RequestBody` / `@ModelAttribute`）校验：参数前加 `@Valid` 即触发（或 `@Validated` 无分组效果一样）。
- **非 Bean 参数**（`@RequestParam` / `@PathVariable`）校验：须**类级** `@Validated` + 参数级约束注解（`@Min` / `@Pattern` 等）。
- **分组校验**：参数前 `@Validated(Group.class)`（指定 groups）。

## 三、Bean 参数校验（`@RequestBody`）

```java
@PostMapping
public Result create(@Valid @RequestBody UserCreateDTO dto) {  // @Valid 触发校验
    return userService.create(dto);
}

public class UserCreateDTO {
    @NotBlank
    @Length(min = 3, max = 20)
    private String username;

    @ValidPhone                           // 组合注解（见下方「组合注解」），不散落正则
    private String phone;

    @Email
    private String email;

    @NotNull
    @Min(18) @Max(120)
    private Integer age;

    @Valid                                // 嵌套对象校验（级联）
    private AddressDTO address;

    @Valid                                // 集合元素校验
    private List<@Valid OrderDTO> orders;
}
```

> 校验失败抛 `MethodArgumentNotValidException`（`@RequestBody`）或 `ConstraintViolationException`（非 Bean 参数）→ 用全局异常处理捕获（见 `05-exception-handling.md`）。

### 错误消息：用 `ValidationMessages.properties` 插值（不在注解里硬编码）

注解里的 `message = "用户名不能为空"` 是**硬编码**——改文案要改代码、不支持国际化、DTO 里堆满字符串。**推荐用 properties 文件插值**：

```properties
# src/main/resources/ValidationMessages.properties（默认）
user.username.notblank=用户名不能为空
user.username.length=用户名长度需在 {min}-{max} 字符
user.phone.invalid=手机号格式不正确
```
```properties
# src/main/resources/ValidationMessages_en.properties（英文，可选）
user.username.notblank=Username must not be blank
```

```java
// 注解里只写 key，{min}/{max} 等占位符自动注入约束参数
@NotBlank(message = "{user.username.notblank}")
@Length(min = 3, max = 20, message = "{user.username.length}")
private String username;
```

> **规则**：`message` 写 `{key}`（指向 `ValidationMessages.properties`），不硬编码中文串。占位符 `{min}`/`{max}`/`{value}` 由校验器自动从注解属性注入。properties 文件须用 UTF-8（中文）。

### 组合注解：复用校验规则，不到处复制正则

像手机号、邮箱、身份证这类**反复出现的校验模式**，不要在每个字段上重复贴 `@Pattern(regexp=...)`——用**组合注解**封装一次，到处复用：

```java
// 1. 定义组合注解（@Constraint(validatedBy = {}) 表示无需自定义校验器，纯组合）
@NotBlank
@Pattern(regexp = "^1[3-9]\\d{9}$", message = "{phone.invalid}")
@Size(min = 11, max = 11)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Constraint(validatedBy = {})              // 关键：组合注解，不写校验器
public @interface ValidPhone {
    String message() default "{phone.invalid}";   // 默认指向 properties
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

// 2. 使用（任意字段一行搞定，不复制正则）
public class UserCreateDTO {
    @ValidPhone
    private String phone;
    // @ValidIdCard / @ValidBankCard 同理封装
}
```

> **何时用组合注解**：同一校验模式（正则 + 长度 + 非空）在 **≥2 个字段/类**出现。只用一次的字段直接贴原生注解即可。
>
> **组合注解三要素**（JSR303 规定）：`message()` / `groups()` / `payload()`，缺一编译失败。`@Constraint(validatedBy = {})` 区分「组合注解」（空数组）vs「自定义校验器」（见下方第七节）。

#### 组合注解的「多报一」坑（实跑验证）

**默认行为**：组合注解（`@Constraint(validatedBy = {})`）会报告**每个**组成注解的违反——如 `@ValidPhone` 里的 `@Pattern` + `@Size` 都不满足时，会返回两条错误（「手机号格式不正确」+「个数必须在11和11之间」）。

**只报一条**：加 `@ReportAsSingleViolation`，校验失败时只报组合注解自身的 `message`，不透出内部子注解的违反：

```java
@NotBlank
@Pattern(regexp = "^1[3-9]\\d{9}$", message = "{phone.invalid}")
@Size(min = 11, max = 11)
@ReportAsSingleViolation                     // 只报组合注解的 message，不报子注解
@Constraint(validatedBy = {})
public @interface ValidPhone { ... }
```

> **何时加 `@ReportAsSingleViolation`**：组成注解是「同一校验的多个侧面」（如手机号的正则 + 长度都是「格式」），用户只关心「格式对不对」一条结论。若组成注解是独立维度（如 `@NotNull` + `@Email`，空值和格式是不同问题），则**不加**，让每条独立报。

## 四、非 Bean 参数校验（`@RequestParam` / `@PathVariable`）

```java
@RestController
@Validated                              // ✗✗✗ 必须类级标 @Validated，否则参数校验不触发
public class UserController {

    @GetMapping("/{id}")
    public Result get(@PathVariable @Min(1) Long id) {  // 参数级约束
        return userService.getById(id);
    }

    @GetMapping("/search")
    public Result search(
        @RequestParam @Pattern(regexp = "^[a-z]+$") String keyword,  // 参数级约束
        @RequestParam @Min(1) @Max(100) Integer size) {
        return userService.search(keyword, size);
    }
}
```

> **坑**：非 Bean 参数校验须**类级 `@Validated`**。只标参数约束注解（`@Min` / `@Pattern`）而类上无 `@Validated`，**校验静默失效**（无报错、不拦截）。这是最高频的「校验没生效」原因。

## 五、分组校验（Create / Update 分离）

```java
// 1. 定义分组接口
public interface Create {}
public interface Update {}

// 2. DTO 上用 groups 区分
public class UserDTO {
    @Null(groups = Create.class)                    // 新增时须为 null（DB 自增）
    @NotNull(groups = Update.class)                 // 修改时必填
    private Long id;

    @NotBlank(groups = {Create.class, Update.class})// 两组都校验
    private String username;
}

// 3. Controller 指定 groups
@RestController
@Validated
public class UserController {

    @PostMapping
    public Result create(@Validated(Create.class) @RequestBody UserDTO dto) { ... }

    @PutMapping
    public Result update(@Validated(Update.class) @RequestBody UserDTO dto) { ... }
}
```

### 坑：分组校验不触发

| ✗ 错误写法 | 原因 |
|---|---|
| 类级 `@Validated` + 参数前 `@Valid`（标准注解） | `@Valid` 无 groups 参数，校验全部约束（不分组） |
| 类级 `@Validated(Create.class)` + 参数前 `@Valid` | 类级 `@Validated` 的 groups **不作用于参数 Bean**（类级 `@Validated` 只管非 Bean 参数 + 方法级校验） |
| 参数前 `@Validated(Create.class)` 但类无 `@Validated` | 参数 Bean 分组靠**参数前 `@Validated(Group.class)`**，类级 `@Validated` 不强制要求（但非 Bean 参数校验时需要） |

```java
// ✓ 正确：参数前 @Validated(Group.class) 指定分组
@PostMapping
public Result create(@Validated(Create.class) @RequestBody UserDTO dto) { ... }
```

### 默认分组（`Default.class`）

- 未指定 groups 的约束属于 `Default.class`。
- `@Validated(Create.class)` **只校验** `Create.class` 组的约束，**不校验** `Default.class`（无 group 的约束被跳过）。
- 想同时校验默认组 + 分组组：`@Validated({Default.class, Create.class})`，或分组接口继承 `Default`：
  ```java
  public interface Create extends Default {}   // Create 组包含 Default 组
  ```

## 六、常用约束注解速查

| 注解 | 作用 | 适用类型 |
|---|---|---|
| `@NotNull` | 非 null | 任意 |
| `@NotEmpty` | 非 null 且非空（集合 / 字符串 / Map） | Collection / String / Map |
| `@NotBlank` | 非 null 且去空格后非空 | String |
| `@Size(min,max)` | 长度 / 元素数 | String / Collection / Map / Array |
| `@Length(min,max)` | 字符串长度（Hibernate Validator） | String |
| `@Min` / `@Max` | 数值范围 | 数字类型 |
| `@Range(min,max)` | 范围（Hibernate Validator） | 数字类型 |
| `@Pattern(regexp)` | 正则匹配 | String |
| `@Email` | 邮箱格式 | String |
| `@Past` / `@Future` | 过去 / 未来日期 | Date / 时间类型 |
| `@DecimalMin` / `@DecimalMax` | 十进制范围 | BigDecimal / String |
| `@Positive` / `@Negative` | 正 / 负 | 数字 |
| `@AssertTrue` / `@AssertFalse` | 布尔断言 | Boolean |

## 七、自定义校验器

```java
// 1. 定义注解
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = PhoneValidator.class)        // 绑定校验器
public @interface Phone {
    String message() default "手机号格式错";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

// 2. 实现校验器
public class PhoneValidator implements ConstraintValidator<Phone, String> {
    private static final Pattern P = Pattern.compile("^1[3-9]\\d{9}$");
    @Override
    public boolean isValid(String value, ConstraintValidatorContext ctx) {
        if (value == null) return true;                // null 由 @NotNull 管，不重复
        return P.matcher(value).matches();
    }
}

// 3. 使用
public class UserDTO {
    @Phone
    private String phone;
}
```

> 三要素（`message` / `groups` / `payload`）同第五节组合注解。

## 八、校验失败异常处理

| 参数类型 | 校验失败异常 |
|---|---|
| `@RequestBody`（Bean） | `MethodArgumentNotValidException` |
| `@RequestParam` / `@PathVariable`（非 Bean） | `ConstraintViolationException` |
| 方法返回值校验 | `MethodArgumentNotValidException` |

捕获与统一返回见 `05-exception-handling.md`。
