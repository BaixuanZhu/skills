# 05 · 全局异常处理

> `@RestControllerAdvice` + `@ExceptionHandler` 的核心坑：匹配顺序、兜底、校验异常捕获、Filter/异步异常不进处理器。

## 一、统一返回体（跟随项目约定，不另造）

**先 grep 现有 Controller 返回类型**——团队已有 `Result` / `R` / `ApiResponse` 就用现有的。无约定时用最小模板：三字段 `code` / `message` / `data` + `success(data)` / `error(code,msg)` 两个工厂方法。

## 二、最小可用 `@RestControllerAdvice`

只需处理三类异常，其余按需扩展：

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    // 1. 业务异常（自定义，返回业务码）
    @ExceptionHandler(BusinessException.class)
    public Result<Void> handleBusiness(BusinessException e) {
        return Result.error(e.getCode(), e.getMessage());
    }

    // 2. 参数校验异常（@RequestBody Bean）
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Result<Void> handleValid(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getFieldErrors().stream()
            .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
            .collect(Collectors.joining("; "));
        return Result.error(400, msg);
    }

    // 3. 兜底（必须最后——见下方顺序坑）
    @ExceptionHandler(Exception.class)
    public Result<Void> handleAll(Exception e) {
        log.error("未知异常", e);
        return Result.error(500, "服务器内部错误");
    }
}
```

### 其他常见异常（按需加，无需全列）

| 异常 | 场景 | 处理 |
|---|---|---|
| `ConstraintViolationException` | `@RequestParam`/`@PathVariable` 校验失败（非 Bean） | 返回 400 + 约束消息 |
| `MethodArgumentTypeMismatchException` | 参数类型转换错（`?id=abc` 转 Long 失败） | 返回 400 |
| `MissingServletRequestParameterException` | 缺少必填参数 | 返回 400 |
| `HttpRequestMethodNotSupportedException` | 请求方法不支持 | 返回 405 |

## 三、核心坑：`@ExceptionHandler` 匹配顺序

### 同类内：按异常类型「最近匹配」（非代码顺序）

Spring 找**最精确**的异常类型匹配。抛 `BusinessException` 时，同时注册了 `Exception.class` 和 `BusinessException.class` → 走后者（距离近）。**代码声明顺序不影响同类匹配结果。**

### 跨类（多个 `@RestControllerAdvice`）：`@Order` 决定查找顺序

```java
@RestControllerAdvice @Order(1)   // 高优先级
class SpecificHandler {
    @ExceptionHandler(BusinessException.class) ...   // 精确
}

@RestControllerAdvice @Order(2)   // 低优先级
class GenericHandler {
    @ExceptionHandler(Exception.class) ...           // 兜底
}
```

> **陷阱**：兜底类（含 `Exception.class`）若 `@Order` 更高（数字更小），`BusinessException` 会被它的 `Exception.class` **先匹配走**，精确处理器永远不执行。
>
> **解法**：兜底类 `@Order(Ordered.LOWEST_PRECEDENCE)`，或合并到一个 Advice 类内（同类按类型距离匹配，无此问题）。

## 四、自定义业务异常

```java
public class BusinessException extends RuntimeException {   // 继承 RuntimeException（非受检）
    private final int code;
    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
    }
    public int getCode() { return code; }
}
```

- **继承 `RuntimeException`**：不强制 try-catch，由全局兜。继承受检 `Exception` 则处处声明 `throws`，污染 Service 签名。
- **Service 内直接 `throw new BusinessException(40901, "用户名已存在")`**。

## 五、异常处理捕获不到的场景（操作性，高频踩坑）

| 异常来源 | 进 `@ExceptionHandler`？ | 解法 |
|---|---|---|
| Controller 抛的 | ✓ | 走 `HandlerExceptionResolver` 链 |
| `@ExceptionHandler` 内再抛的 | ✗（递归） | 处理器内 try-catch |
| **Filter / Interceptor 抛的** | ✗ | 在 DispatcherServlet 之前；自定义 `ErrorController` 或 Filter 内 try-catch 写 response |
| **`@Async` 方法抛的** | ✗ | 异步线程异常不传播；用 `AsyncUncaughtExceptionHandler`（见 `07-async-schedule.md`） |
| Sa-Token 过滤器抛的 | ✗ | → sa-token-dev（须 `.setError()`） |

## 六、`ResponseEntity` vs 统一返回体（一行决策）

- **跟随项目既有风格**，不混用。
- 用 `Result<T>` 的项目，异常也返回 `Result`；用 `ResponseEntity` 的项目，异常返回 `ResponseEntity`（状态码 + body）。
- `Result<T>`：前端统一处理（永远 HTTP 200 + code 判断）。
- `ResponseEntity`：HTTP 状态码语义化（404/409/500），RESTful 风格。

## 七、`@RestControllerAdvice` 限定范围（多模块时）

```java
@RestControllerAdvice("com.app.controller")                    // 限定包
@RestControllerAdvice(annotations = RestController.class)       // 限定注解
```

不限定则处理所有 Controller。微服务多模块时限定包，避免跨模块 Advice 互相干扰。
