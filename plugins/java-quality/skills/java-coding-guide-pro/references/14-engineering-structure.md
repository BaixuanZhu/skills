# 14 · 工程组织与职责划分

> **判据**：代码能跑通、测试能过，但**边界、归属、职责**放错——改动一处牵连多处、想复用只能复制粘贴。
> **定级 A**：只约束**新生成代码**；审查/修改既有代码时不主动改写、不发起询问。
> 与相邻文件的分工：`06` 管对象拷贝，`11` 管命名/OOP/常量放置，`12` 管方法与认知复杂度——**本文只管「东西该放在哪、谁该干什么」**。
> **核心原则：多写几行代码不是成本，职责错位才是成本。** 为一个清晰边界多写 20 行显式代码，永远优于靠隐式约定省 5 行。

## 一、分层与边界

### 1. 三层各只做自己的事

| 层 | 只做 | 禁止 |
|---|---|---|
| Controller | 参数校验（`@Valid`）、协议转换、调 Service、组装响应 | 业务规则、直接调 DAO、写事务、拼 SQL |
| Service | 业务规则、事务边界、多步编排 | 感知 Servlet 对象（`HttpServletRequest/Response`）、直接拼 HTTP 响应体、操作文件路径 |
| DAO / Mapper | 单表数据访问 | 业务判断（`if` 业务规则）、跨表组装业务对象 |

```java
// ✗ Controller 里写业务规则 + 直连 DAO
@PostMapping("/order")
public Result create(@RequestBody OrderDTO dto) {
    if (dto.getAmount().compareTo(BigDecimal.ZERO) <= 0) return Result.fail("金额非法");
    orderDao.insert(toEntity(dto));
    return Result.ok();
}
```
```java
// ✓ Controller 只做协议转换 + 调 Service
@PostMapping("/order")
public Result<OrderVO> create(@Valid @RequestBody OrderCreateDTO dto) {
    return Result.ok(orderService.create(dto));
}
```
> 判据：**把 Controller 整个删掉、换成 MQ 消费者/定时任务，业务还能跑吗**——不能，说明业务逻辑写错层了。

### 2. Entity 不出持久层

```java
// ✗ 直接把 Entity 返回给前端
@GetMapping("/user/{id}")
public User getUser(@PathVariable Long id) { return userDao.selectById(id); }
```
> 两个后果：① 密码哈希、盐、内部标记等字段**直接外泄**；② 表字段改名 → 对外接口契约被动破坏。即使 `@JsonIgnore` 屏蔽也是补丁——契约仍与表结构绑定。

```java
// ✓ Entity → DTO/VO 显式转换（编译期类型安全，见 06）
@GetMapping("/user/{id}")
public UserVO getUser(@PathVariable Long id) { return userService.getVo(id); }
```
> 三层数据对象各司其职：`DO/Entity`（表结构）、`DTO`（入参，带校验注解）、`VO`（出参，只含要暴露的字段）。转换**用 MapStruct 或显式构造器**，禁反射拷贝（见 `06`）。

### 3. 事务边界在 Service，且事务内不做外部 IO

```java
// ✗ 事务开在 Controller（顺带把响应序列化也包进事务）
@Transactional
@PostMapping("/order")
public Result create(...) { ... }
```
```java
// ✗ 事务持 DB 连接期间调 RPC / 发消息 / 写文件
@Transactional
public void pay(Order o) {
    orderDao.update(o);
    payClient.call(o);                 // ✗ 外部 IO 在事务内，连接被占住
}
```
```java
// ✓ 事务只包 DB 操作，外部调用放事务外
public void pay(Order o) {
    updateInTx(o);                     // 独立事务方法
    payClient.call(o);                 // 事务外
}
```
> 事务内做外部调用会延长持连接时间，高并发下连接池耗尽——现场表现是「随机超时」而非报错。同类：事务内循环单条写库（改批量写）、事务内 `Thread.sleep`。

## 二、封装

### 4. 依赖用构造器注入 + `final`

```java
// ✗ 字段注入：依赖隐藏、字段可被替换、循环依赖拖到运行期才炸
@Service
public class OrderService {
    @Autowired private OrderDao orderDao;
    @Autowired private PayClient payClient;
}
```
```java
// ✓ 构造器注入：依赖显式、字段 final 不可变、循环依赖启动即失败
@Service
public class OrderService {
    private final OrderDao orderDao;
    private final PayClient payClient;

    public OrderService(OrderDao orderDao, PayClient payClient) {
        this.orderDao = orderDao;
        this.payClient = payClient;
    }
}
```
> 单构造器时 Spring 自动注入，无需 `@Autowired`。**好处是编译期可见的**：类要什么依赖一眼看全，单测直接 new 传 mock。**依赖个数不是职责判据**——复杂业务里一个 Service 注入 6~8 个协作者属正常编排（判据见 §四 9）。

### 5. 状态私有，变更走有语义的方法

```java
// ✗ public 字段 / 全参 setter：任何地方都能改，校验无处安放
public class Account {
    public BigDecimal balance;
    public void setBalance(BigDecimal b) { this.balance = b; }
}
```
```java
// ✓ 状态私有，规则内聚在对象自己身上
public class Account {
    private BigDecimal balance = BigDecimal.ZERO;

    public BigDecimal getBalance() { return balance; }

    public void withdraw(BigDecimal amt) {
        if (amt.signum() <= 0) throw new BizException("金额必须为正");
        if (balance.compareTo(amt) < 0) throw new BizException("余额不足");
        this.balance = balance.subtract(amt);
    }
}
```
> 判据：**一个类的字段若只被外部 setter 直接改，它就是个数据袋**——校验散到了所有调用方，改一次规则要改 N 处。`record`（JDK 16+）适合 DTO/VO 这类纯载体，不适用于有行为不变量的领域对象。

## 三、常量与配置归属

### 6. 环境相关的一律外置到配置

```java
// ✗ 环境相关的值写死在业务类：换环境、调参数都要改代码重新发版
public class PayService {
    private static final String CALLBACK_URL = "https://api.pay.com/notify";
    private static final int    TIMEOUT_MS   = 5000;
    private static final boolean NEW_FLOW_ON = true;
}
```
```java
// ✓ 外置配置，按域分组绑定
@ConfigurationProperties(prefix = "pay")
public class PayProperties {
    private String callbackUrl;
    private Duration timeout = Duration.ofSeconds(5);
    private boolean newFlowEnabled;
    // getter / setter
}
```
```yaml
pay:
  callback-url: https://api.pay.com/notify
  timeout: 5s
  new-flow-enabled: true
```
> 判据：**换环境或调参数是否需要改代码**——需要，就必须外置。常被漏掉的四类：回调/第三方 URL、超时（连接/读/任务）、功能开关与灰度比例、业务阈值（重试上限、单笔限额）。密钥/口令走环境变量或 KMS，禁硬编码（见 `07`）。

### 7. 常量放哪：三问定位置

| 问 | 答 → 放置 |
|---|---|
| 谁会用到它？ | 只有本方法 → 方法内 `static final`；只在本类 → 本类 `private static final`；跨类/跨包 → 包级或按域拆分的常量类（`OrderConstants`） |
| 取值是否有限且有语义？ | 是 → `enum`（状态、类型、错误码） |
| 是否随环境变化？ | 是 → 配置文件 / 配置中心（见 §三 6） |

```java
// ✗ 常量堆在实现类里，别的 Service 要用只能复制一份
@Service
public class OrderServiceImpl {
    private static final int    MAX_RETRY  = 3;
    private static final String STATUS_NEW = "NEW";
}
```
```java
// ✓ 按域提出去，共享且单一来源
public enum OrderStatus { NEW, PAID }
public final class OrderConstants {
    public static final int MAX_RETRY = 3;
    private OrderConstants() { }       // 常量类禁实例化
}
```
> 完整的「共享范围 → 放置位置」五级表见 `11-conventions.md` §常量与字面量。**禁 `Constants` 万能类**（所有域堆一起，改一处全量重编译）。

### 8. 配置对象按域聚合，禁 `@Value` 撒满业务类

```java
// ✗ 每个用到的地方各写一遍 @Value，配置项改名要全局搜字符串
@Service public class OrderService  { @Value("${order.timeout}") private long timeout; }
@Service public class RefundService { @Value("${order.timeout}") private long timeout; }
```
```java
// ✓ 一个域一个配置对象，需要它的类注入该对象
@Service
public class OrderService {
    private final OrderProperties props;         // 构造器注入
    public OrderService(OrderProperties props) { this.props = props; }
}
```
> 好处：配置项集中可见、IDE 可跳转、支持 `@Validated` 校验、能在配置类里写默认值与派生逻辑。单个零散配置（如某工具类的开关）用 `@Value` 无妨。

## 四、类与方法的职责

### 9. 类职责单一（God Class：从业务逻辑判定，不看数字）

**主判据——业务视角三问，任一答「否」即说明混了多个概念：**

1. **能否用一句不含「以及」的业务语言说清它是什么？** 「订单服务」可以；「订单和支付服务」不可以。
2. **它的方法是否服务于两个以上互不相关的业务概念？** 判断单位是**业务概念，不是方法个数**——`createOrder` 与 `cancelOrder` 同属订单域，不算多；`createOrder` 与 `sendSms` 分属两个域。
3. **变更原因是否来自多个不同业务方？** 运营改活动规则、财务改对账口径、客服改工单流程都落在同一个类上 → 上帝类。（SRP 的原始定义：一个类只应有一个变更原因。）

**辅助信号（出现则看一眼，单独出现不构成判据）：**

- 类名或 javadoc 必须用「And / 以及」才能概括职责；
- 方法能按业务对象干净地分成两组以上（`orderXxx` / `refundXxx`），且两组之间不共享字段；
- 类内字段分别维护两个不相关聚合的状态（同时持有 `Order`、`SmsTemplate`、`AuditLog` 的生命周期）。

**明确不作为判据：**

- **注入依赖个数**——复杂业务里一个 Service 正常注入 6~8 个协作者（库存、支付、优惠券、风控、物流），它只负责编排本域流程，仍是单一职责。拿数字卡会把正常代码误判成上帝类。
- **类行数、public 方法数**——只是「值得看一眼」的温度计，阈值随业务复杂度浮动，不能当门禁。

```java
// ✗ 上帝类：五个方法分属五个互不相关的业务域，变更原因来自五个业务方
@Service
public class OrderService {
    public void createOrder(...) { }    // 订单域
    public void refund(...)      { }    // 售后域
    public void pay(...)         { }    // 支付域
    public void sendSms(...)     { }    // 通知域
    public void syncToErp(...)   { }    // 外部集成域
}
```
```java
// ✓ 依赖多但职责单一：六个协作者全在「创建订单」这一个业务概念内，是编排不是混合
@Service
public class OrderCreateService {
    private final InventoryService    inventory;
    private final PricingService      pricing;
    private final CouponService       coupon;
    private final RiskService         risk;
    private final OrderRepository     orderRepository;
    private final OrderEventPublisher publisher;

    public OrderVO create(OrderCreateDTO dto) { ... }   // 只做「创建订单」这一件事
}
```
> 对比点：前者五个方法分属**五个业务域**；后者六个依赖**同属一个业务概念**。**依赖个数不说明问题，「是否同一业务概念」才说明问题。**
> 拆法：按**业务概念**拆（订单 / 支付 / 通知），不是按「每组几个方法」平均分。
> 与 `12` 的分工：`12` 管**方法**的认知复杂度，本文管**类**的职责边界。方法拆得再干净，一个把三个业务域揉在一起的 `Manager` 依旧不可维护。

### 10. 方法只做一件事（抽象层次一致）

```java
// ✗ 一个方法里既有编排又有细节，跨越校验/计算/持久化/通知四个层次
public void handle(Order o) {
    if (o.isValid()) {
        BigDecimal fee = o.getAmount().multiply(RATE).setScale(2, RoundingMode.HALF_UP);
        jdbcTemplate.update("update t_order set fee = ? where id = ?", fee, o.getId());
        mailSender.send(o.getEmail(), "费用已更新");
    }
}
```
```java
// ✓ 主流程只编排，每步一个语义方法
public void handle(Order o) {
    if (!o.isValid()) return;
    BigDecimal fee = calcFee(o);
    orderDao.updateFee(o.getId(), fee);
    notifyService.feeChanged(o, fee);
}
```
> 复用手法见 `12-complexity.md` 手法 2（提炼语义方法）+ 手法 1（卫语句早返回）。判据：**不读被调方法体，能否看懂这个方法在干什么**。

## 五、复用与去重

### 11. 同一逻辑出现 ≥2 处即提炼

```java
// ✗ 同一段判断在两个类各写一遍（改一处忘一处）
class OrderService  { private boolean ok(User u) { return u != null && u.isActive() && !u.isLocked(); } }
class RefundService { private boolean ok(User u) { return u != null && u.isActive() && !u.isLocked(); } }
```
```java
// ✓ 提到内聚度最高的位置：领域对象自身
public class User {
    private boolean active;
    private boolean locked;
    public boolean isOperable() { return active && !locked; }
}
// 使用：if (!user.isOperable()) return;
```
> 判据与 `11` §常量与字面量一致：**同一逻辑 ≥2 处即提炼**。优先级：**领域对象自身**（内聚最高、可单测）> 包内工具类 > 跨包工具类。禁跨域塞 `CommonUtil`。

### 12. 反向：禁无语义抽象与过度泛化

```java
// ✗ 把两个只因"长得像"的逻辑抽成一个带 flag 的方法
public Result handle(Object input, boolean isOrder, boolean isRefund) { ... }

// ✗ 只有一个调用方的"通用组件"+ 复杂泛型签名
public <T, R, C extends Collection<T>> Map<T, R> toMap(C src,
        Function<T, R> keyFn, Function<T, R> valFn) { ... }
```
```java
// ✓ 按"概念是否相同"决定合并；只有一处用的代码就地留着
private Result handleOrder(Order o)  { ... }
private Result handleRefund(Refund r) { ... }
```
> 判据：**两条逻辑是否表达同一个业务概念**——是则合并，只是代码形似则分开。带 `boolean flag` 分支的方法、`(Object, Object...)` 签名都是抽象错的信号。这与 `12-complexity.md` 的 `doPart1/doPart2` 假修复同源：**为过门禁/为消灭重复而抽象，复杂度只是被藏起来**。

## 六、资源归属

### 13. 重资源对象归应用级单例，生命周期托管

```java
// ✗ 业务方法内 new 线程池：每次调用建一个池，永不关闭 → 线程/内存泄漏
public void asyncRun(List<Task> tasks) {
    ExecutorService pool = new ThreadPoolExecutor(10, 10, 0L, TimeUnit.MILLISECONDS,
            new LinkedBlockingQueue<>(100));
    tasks.forEach(t -> pool.submit(() -> run(t)));
    // 没有 shutdown
}
```
```java
// ✓ 应用级 Bean 单例 + 容器托管生命周期
@Configuration
public class AsyncConfig {
    @Bean(destroyMethod = "shutdown")        // 容器关闭时自动 shutdown
    public ExecutorService bizExecutor() {
        ThreadFactory tf = new ThreadFactory() { /* 命名线程，见 05 */ };
        return new ThreadPoolExecutor(10, 10, 0L, TimeUnit.MILLISECONDS,
                new LinkedBlockingQueue<>(100), tf, new ThreadPoolExecutor.CallerRunsPolicy());
    }
}
```
> 必须按应用级单例复用的对象：**线程池**（见 `05`）、**HTTP 客户端**（见 `04`）、**`ObjectMapper`**（见 `04`）、**连接池/数据源**、**`SecureRandom`**（见 `08`）、**`DateTimeFormatter`**。
> 判据：**创建开销大 + 有内部状态或池化资源 → 归应用级**，不在业务方法里 `new`；有 `close`/`shutdown` 的交给容器托管。

### 14. 工具类只放无状态纯函数

```java
// ✗ 工具类里持有状态 / 反向依赖业务 Service
public class OrderUtil {
    private static SimpleDateFormat SDF = new SimpleDateFormat("yyyyMMdd");  // ✗ 非线程安全静态状态
    @Autowired private static OrderService orderService;                     // ✗ 静态注入恒为 null（见 13）
    public static String genNo() { ... }                                     // ✗ 依赖业务逻辑
}
```
```java
// ✓ 工具类 = final class + 私有构造 + 全部 static 无状态纯函数
public final class OrderNoUtil {
    private OrderNoUtil() { }
    public static String format(LocalDate date, long seq) {
        return date.format(DateTimeFormatter.BASIC_ISO_DATE) + String.format("%07d", seq);
    }
}
```
> 需要状态或依赖 → 它是组件（`@Component`），不是工具类。**工具类里出现 `static` 可变字段 = 必然的并发 bug**（见 `05`）；出现 `@Autowired` = 恒为 null（见 `13`）。
