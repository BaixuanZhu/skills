# 13 · 静默失效（编译过、单测过、运行不报错）

> **判据**：编译期通过 + 单测通过 + 运行期不抛异常，但**行为不符合预期**。AI 生成代码高发，代码评审也极易漏掉。
> 本文全部为 **S 级**：新代码禁止；审查/修改既有代码时命中 → 立即向用户提出。
> 与相邻文件的分工：`11` 管命名与 OOP 规约，`12` 管认知复杂度，`14` 管职责划分与归属——**本文只收「不报错但不生效」**。

## 一、Spring 代理边界（最隐蔽）

### 1. `@Transactional` / `@Async` / `@Cacheable` 自调用失效

```java
// ✗ 同类内 this 调用不走代理 → 三个注解全部静默失效
@Service
public class OrderService {
    public void create(Order o) {
        this.save(o);                 // ✗ 直接 this 调用，@Transactional 不生效
    }
    @Transactional
    public void save(Order o) { ... }
}
```
> 无任何报错，事务根本没开：前半段写库成功、后半段失败后不回滚。

```java
// ✓ 方案A（首选）：拆到另一个 Bean，跨 Bean 调用必然走代理
@Service
public class OrderCreator {
    private final OrderWriter writer;                     // 构造器注入
    public OrderCreator(OrderWriter writer) { this.writer = writer; }
    public void create(Order o) { writer.save(o); }        // ✓ 走代理
}

// ✓ 方案B：同一事务内需多步时，用 TransactionTemplate 显式包裹
private final TransactionTemplate txTemplate;
public void create(Order o) {
    txTemplate.execute(status -> { doStep1(o); doStep2(o); return null; });
}
```
> 自注入自身（`@Lazy`）也能绕过，但属 workaround——优先拆 Bean 或用 `TransactionTemplate`。

### 2. 事务方法内 `catch` 吞异常 → 不回滚

```java
// ✗ 异常被吃掉，容器感知不到 → 事务照常提交，脏数据落库
@Transactional
public void transfer(Long from, Long to, BigDecimal amt) {
    try {
        deduct(from, amt);
        add(to, amt);
    } catch (Exception e) {
        log.error("转账失败", e);        // ✗ 吞掉，不回滚
    }
}
```
```java
// ✓ 继续抛出，由容器回滚
catch (Exception e) {
    log.error("转账失败", e);
    throw e;
}
// ✓ 业务上必须吞异常时，显式标记回滚
catch (Exception e) {
    log.error("转账失败", e);
    TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
}
```
> 默认只对 `RuntimeException`/`Error` 回滚；受检异常需 `@Transactional(rollbackFor = Exception.class)`。**catch 不吞 + 受检异常配 rollbackFor，两条要同时满足。**

### 3. 注解打在 `private` / `final` / `static` 方法上

```java
// ✗ 代理无法覆写这些方法 → 注解彻底失效
@Transactional
private void save(Order o) { ... }      // ✗ 永远没有事务
```
```java
// ✓ 注解方法必须 public 且非 final/static（CGLIB 要能覆写）
@Transactional
public void save(Order o) { ... }
```
> IDE 不报、启动不报、跑起来也不抛异常——这是最难自查的一条。类内 `private` 方法带事务注解，最常见。

### 4. `@Value` / `@Autowired` 注静态字段

```java
// ✗ 静态字段不属于任何实例，注入代码永不执行 → 恒为 null
@Component
public class SmsClient {
    @Value("${sms.url}") private static String url;      // ✗ 永远 null
    @Autowired private static RedisTemplate rt;          // ✗ 永远 null
}
```
```java
// ✓ 实例字段 + 构造器注入（final 不可变）
@Component
public class SmsClient {
    private final String url;
    public SmsClient(@Value("${sms.url}") String url) { this.url = url; }
}
```
> 想保留 static 只能靠 `@PostConstruct` 手动搬运，那是 workaround——直接改成实例字段。

## 二、类型与拆箱

### 5. 包装类型 `==` 时真时假（`Integer` 缓存）

```java
// ✗ 包装类 == 比的是引用；Integer 缓存只覆盖 -128~127
Integer a = 128, b = 128;
boolean same = (a == b);                                   // false！（换成 127 就是 true）
if (order.getStatus() == OrderStatus.PAID.getCode()) { }   // ✗ 静默为 false
```
```java
// ✓ Objects.equals；或先取原始类型再比
if (Objects.equals(order.getStatus(), OrderStatus.PAID.getCode())) { }
int code = OrderStatus.PAID.getCode();                     // 取 int 后再比
if (order.getStatus() == code) { }
```
> 小数据量测试全过，数据上量后随机为 false——边界 127/128 是经典陷阱。`Long` 同理（缓存 -128~127 可用 `Long.valueOf`，超出即 false）。

### 6. 自动拆箱 NPE（错位暴露）

```java
// ✗ key 缺失 → get 返回 null → 拆箱 NPE，且异常点偏离问题点
Map<String, Integer> stock = ...;
int n = stock.get(skuId);                                  // ✗ 缺失时 NPE
```
```java
// ✓ getOrDefault / 显式判空
int n = stock.getOrDefault(skuId, 0);
int n = Optional.ofNullable(stock.get(skuId)).orElse(0);
```
> 同族：`Integer i = null; if (i > 0)`、三元表达式两分支类型不同（`Integer` 与 `int`）触发拆箱、`Boolean` 直接参与 `if` 等。

## 三、集合与并发容器

### 7. `containsKey` + `put` 两段式（非原子）

```java
// ✗ 两段之间非原子：并发下两个线程都判断为"不存在" → 后写覆盖先写（丢更新）
if (!map.containsKey(k)) { map.put(k, new ArrayList<>()); }
// ✗ 同族：先 get 判空再 put
if (map.get(k) == null) { map.put(k, init()); }
```
```java
// ✓ 单次原子操作
map.computeIfAbsent(k, key -> new ArrayList<>());
map.putIfAbsent(k, init());
map.merge(k, 1, Integer::sum);                             // 计数
```
> `ConcurrentHashMap` 的**单个方法**是原子的，「先查后写」两段拼起来不是。这个坑在压测才暴露，功能测试永远发现不了。

### 8. `List.of` / `Map.of` / `Arrays.asList` 的可变性各不相同

```java
// ✗ 三种"不可变"语义不同，误判即运行期异常
List<String> a = List.of("a", "b");
a.add("c");                                                // ✗ UnsupportedOperationException（全不可变）

List<String> b = Arrays.asList("a", "b");
b.set(0, "x");                                             // ✓ 可以（替换）
b.add("c");                                                // ✗ 抛异常（固定大小，非不可变）
```
```java
// ✓ 需要可变 → 显式包一层
List<String> a = new ArrayList<>(List.of("a", "b"));
a.add("c");                                                // ✓
```
> 四者可变性对照：`Arrays.asList`（**固定大小**：`set` 可、`add`/`remove` 不可）、`List.of`/`Map.of`（**全不可变**）、`Collectors.toList()`（**可变**）、`Stream.toList()`（**不可变**，JDK 16+）。API 返回 `List` 时若内部用的是 `of` 系，调用方一改就炸。

### 9. `split` 丢弃尾空串

```java
// ✗ 不传 limit 时尾随空串全部丢弃，定长字段解析错位
String[] a = "a,b,,".split(",");        // 长度 2（不是 4）
String[] b = ",,a".split(",");          // 长度 3（前导空串保留）
```
```java
// ✓ 需要全部字段（CSV / 定长协议）传负 limit
String[] a = "a,b,,".split(",", -1);    // 长度 4
```
> 同一方法两种行为：**前导空串保留、尾随空串丢弃**。按 `length` 取下标时直接越界或错位。

## 四、实体与 Lombok

### 10. `@Data` 打在实体 / 关联对象上

```java
// ✗ 三个问题同时发生
@Data
@Entity
public class Order {
    private Long id;
    private List<OrderItem> items;      // ✗ 双向关联时 toString 无限递归 → StackOverflowError
    private Boolean deleted;
}
```
```java
// ✓ 实体/领域对象：只读 getter + 显式构造，关联排除 toString/equals
@Getter
@Entity
public class Order {
    private Long id;
    @ToString.Exclude @EqualsAndHashCode.Exclude
    private List<OrderItem> items;
    protected Order() { }               // JPA 需要
    public Order(Long id) { this.id = id; }
}
```
> `@Data` = `@Getter`+`@Setter`+`@ToString`+`@EqualsAndHashCode`+`@RequiredArgsConstructor`。三个后果：① 全字段 setter **破坏封装**（任意处可改，见 `14`）；② 双向关联 `toString`/`hashCode` **无限递归**；③ `@EqualsAndHashCode` 覆盖全部字段（含可变集合）→ 对象放进 `HashSet` 后改字段就再也找不到。
> `@Data` 适合 DTO/VO 这类纯数据载体；**实体/领域对象用 `@Getter` + 显式构造**。

### 11. 返回值直接暴露内部集合

```java
// ✗ 外部拿到内部引用，可绕过校验直接改内部状态
public List<OrderItem> getItems() { return this.items; }
// 调用方 items.clear() → 内部数据被清空，无任何报错
```
```java
// ✓ 返回真正的防御性副本
public List<OrderItem> getItems() { return List.copyOf(this.items); }
```
> `Collections.unmodifiableList(this.items)` 只是**视图**——持有原引用的一方仍能改；`List.copyOf` 是独立副本（对外不可变，且复制后不受后续内部修改影响）。列表元素本身可变时需再做元素级拷贝。

### 12. `equals` 恒为 true / 恒为 false

```java
// ✗ 重写签名写错 → 变成重载，永远走 Object.equals（比引用）
public boolean equals(User other) { ... }                  // ✗ 参数不是 Object
// ✗ 用 == 比 String / 比包装类型
if (name == other.name) { ... }
```
```java
// ✓ 参数必须是 Object，且与 hashCode 成对重写（契约见 11）
@Override public boolean equals(Object o) {
    if (this == o) return true;
    if (!(o instanceof User u)) return false;
    return Objects.equals(id, u.id);
}
```
> 写成 `equals(User)` 时编译器**静默**生成重载方法（`@Override` 能挡住——所以 `@Override` 必加，见 `11`）。此时 `list.contains(u)`、`map.get(u)`、`Set` 去重全部按引用比较，结果静默错误。
