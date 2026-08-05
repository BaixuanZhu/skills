# 09 · 依赖注入与循环依赖

> 构造器注入 vs `@Autowired` vs `@Resource`、`@Qualifier`、循环依赖（2.6+ 默认禁用）、`@Lazy`、`BeanCurrentlyInCreationException`。

## 一、三种注入方式对比

| 方式 | 写法 | 优点 | 缺点 | 推荐 |
|---|---|---|---|---|
| **构造器注入** | 构造器参数 + `final` 字段 | 不可变、易测、启动期发现循环依赖 | 循环依赖会启动失败（但这是优点：暴露设计问题） | **✓ 首选** |
| **`@Autowired` 字段注入** | `@Autowired private XxxService xxx` | 简洁 | 可变、难单测（须反射 set）、隐藏依赖 | ✗ 避免 |
| **`@Autowired` setter 注入** | setter + `@Autowired` | 可重新注入（测试）、可选依赖 | 可变 | 可选依赖用 |

### 构造器注入（推荐）

```java
@Service
@RequiredArgsConstructor                 // Lombok：自动生成 final 字段的构造器
public class UserService {
    private final UserMapper userMapper;          // final + 构造器注入（不可变）
    private final EmailService emailService;
}
```

> **单个构造器可省略 `@Autowired`**（Spring 4.3+）。多个构造器时须在一个上加 `@Autowired`。

### 为什么构造器注入是首选

1. **不可变**：`final` 字段，初始化后不变（线程安全、防误改）。
2. **易测**：单测可直接 `new UserService(mockMapper, mockEmail)`，不须反射。
3. **启动期发现循环依赖**：构造器注入的循环依赖在启动时直接报错（暴露设计问题）；字段注入允许循环依赖（运行时才发现问题）。
4. **依赖显式**：构造器参数列表一目了然依赖什么，`@Autowired` 字段散落各处难统计。

## 二、`@Autowired` vs `@Resource` vs `@Inject`

| 注解 | 来源 | 默认匹配 | 备选 |
|---|---|---|---|
| **`@Autowired`** | Spring（`org.springframework.beans.factory.annotation`） | **按类型** | `@Qualifier` 指定名 |
| **`@Resource`** | JSR250（`jakarta.annotation`） | **按名称**（name 找不到再按类型） | `name` / `type` 属性 |
| `@Inject` | JSR330（`jakarta.inject`） | 按类型 | `@Named` 指定名 |

**选型**：统一用 `@Autowired`（Spring 项目首选）。`@Resource` 在多实现时按名匹配更直观，但跨类型注入时易出错。**项目内统一一种，不混用。**

## 三、多实现：`@Qualifier` 与 `@Primary`

### 同接口多个实现

```java
public interface PaymentService { void pay(BigDecimal amount); }

@Service("alipayService")
public class AlipayService implements PaymentService { ... }

@Service("wechatPayService")
public class WechatPayService implements PaymentService { ... }
```

### 注入时指定（`@Qualifier`）

```java
@Service
public class OrderService {
    @Autowired
    @Qualifier("alipayService")                // 按名指定
    private PaymentService paymentService;
}
```

### 或标记默认（`@Primary`）

```java
@Service
@Primary                                      // 多实现时的默认选择
public class AlipayService implements PaymentService { ... }

// 注入时不指定 @Qualifier → 选 @Primary 的
@Autowired
private PaymentService paymentService;         // → AlipayService
```

> **`@Primary` vs `@Qualifier`**：`@Primary` 在被注入方标（说"我是默认"）；`@Qualifier` 在注入点标（说"我要哪个"）。全局只有一个默认用 `@Primary`；按场景切换用 `@Qualifier`。

### 构造器注入 + `@Qualifier`

```java
@Service
public class OrderService {
    private final PaymentService paymentService;

    public OrderService(
        @Qualifier("alipayService") PaymentService paymentService   // 构造器参数上标
    ) {
        this.paymentService = paymentService;
    }
}
```

## 四、循环依赖

### 什么是循环依赖

```
A 依赖 B，B 又依赖 A → 循环
A → B → C → A → 循环
```

### SpringBoot 2.6+ 默认禁用循环依赖

启动报错关键信息：
```
BeanCurrentlyInCreationException: ...form a cycle...
Action: Relying upon circular references is discouraged and they are prohibited by default.
```
报错含 ASCII 环形依赖图 + `userService ↔ orderService` 等 Bean 名，据此定位循环链路。

### 解法（按推荐度排序）

#### 解法 1：重构消除（**首选**）—— 抽第三方 Bean 打破环

循环依赖几乎都是**设计问题**——把共同依赖抽到第三方 Bean，打破环。这也适用于 `@Transactional` / `@Async` 自调用失效场景（见 `06-transaction.md` 坑 1 解法 1）。

```java
// ✗ 循环：UserService 依赖 OrderService，OrderService 依赖 UserService
class UserService { final OrderService orderService; }   // ↔
class OrderService { final UserService userService; }    // ↔ 循环

// ✓ 重构：抽 UserOrderFacade 承载两者的共同逻辑，打破环
class UserService { final UserOrderFacade facade; }      // 都依赖 Facade
class OrderService { final UserOrderFacade facade; }     // 不互相依赖
class UserOrderFacade { final UserMapper u; final OrderMapper o; }
```

#### 解法 2：`@Lazy`（次选，临时打破启动期循环）

```java
@Service
public class UserService {
    private final OrderService orderService;

    public UserService(@Lazy OrderService orderService) {   // @Lazy：注入代理，启动期不立即解析
        this.orderService = orderService;
    }
}
```

**原理**：`@Lazy` 让 Spring 注入一个代理对象（而非真实 Bean），延迟到首次使用时才解析，打破启动期的循环解析。

> **⚠️ Lombok 陷阱同 `06-transaction.md` 坑 1 解法 2**：`@Lazy` 须在手写构造器参数上，`@RequiredArgsConstructor` 不传 `@Lazy`，启动报 `BeanCurrentlyInCreationException`。

> **`@Lazy` 的正当用途**：① 临时打破循环依赖（重构前的过渡）；② 解决自调用失效（`@Lazy UserService self`）；③ 延迟初始化重 Bean（启动提速）。**不应用 `@Lazy` 掩盖设计问题**——能重构就重构。

#### 解法 3：放开禁令（**不推荐**，掩盖设计问题）

```yaml
spring:
  main:
    allow-circular-references: true            # 放开 2.6+ 的禁令
```


### 注入方式与循环依赖（SpringBoot 2.6+ 默认全禁）

| 注入方式 | 循环依赖行为（2.6+ 默认禁用） |
|---|---|
| **构造器注入** | 启动**直接失败**（无法构造） |
| **字段注入**（`@Autowired private`） | 启动**失败**（2.6+ 禁用后字段注入也报错；旧版用三级缓存容忍） |
| **setter 注入** | 启动**失败**（同上） |

> 2.6 之前字段/setter 注入靠三级缓存"容忍"循环依赖（运行时注入半成品），**掩盖设计问题**。2.6+ 默认 `allow-circular-references=false`，无论哪种注入方式都启动报错——这是改进，逼开发者重构。

## 五、`BeanCurrentlyInCreationException`

```
org.springframework.beans.factory.BeanCurrentlyInCreationException:
Error creating bean with name 'userService':
Requested bean is currently in creation: Is there an unresolvable circular reference?
```

**含义**：构造器注入循环依赖，或字段注入循环依赖且禁令开启。

**处理**：按上节「循环依赖解法」——首选重构，过渡用 `@Lazy`，不开 `allow-circular-references`。

## 六、可选依赖（`required = false`）

```java
@Autowired(required = false)                   // Bean 不存在时注入 null（不报错）
private Optional<FeatureService> featureService;

// 构造器注入用 Optional 更安全
public MyService(Optional<FeatureService> featureService) {
    this.featureService = featureService.orElse(null);
}
```

> **`required = false` vs `Optional<>`**：`Optional<>` 更显式（调用方知道可能不存在），推荐用 `Optional`。

## 七、最佳实践（仅列前文未详述项）

1. **可选依赖用 `Optional<>`**——比 `@Autowired(required = false)` 显式，调用方知道可能不存在。
2. **统一注入注解**：`@Autowired`（Spring 项目）或 `@Resource`（按名匹配偏好时），**不混用**。

> 注入方式选型、多实现 `@Qualifier`/`@Primary`、循环依赖解法——见上文章节。

