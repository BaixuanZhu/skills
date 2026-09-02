# 09 · 现代 Java 语法（版本门控）

> 每个特性都标注**门控 JDK**（以 LTS 为锚点：8/11/17/21/25）。**先用 `SKILL.md` 的 JDK 版本策略确认目标版本**，低于门控的严禁使用。
> JDK 8 是下限——JDK 8 项目**全部禁用本文件特性**（除已属 JDK 8 的 Lambda/Optional/Stream/java.time）。
> **LTS 锚定原则**：22–24 转正的特性统一归入 JDK 25 LTS（括号注明实际转正版本作背景）；非 LTS 不单独门控。preview/incubator 特性不纳入本表。

## 特性门控速查

| 特性 | 门控 JDK |
|---|---|
| Lambda / 方法引用 / `Optional`/`Stream`/`java.time`/`CompletableFuture` | **8** |
| `var` 局部变量类型推断 | **10** |
| JDK 内置 `HttpClient` | **11** |
| `switch` 表达式（箭头、yield） | **14** |
| 文本块 `"""` | **15** |
| `record`（不可变数据载体） | **16** |
| `Stream.toList()` | **16** |
| `instanceof` 模式匹配 | **16** |
| `sealed` 密封类 | **17** |
| 虚拟线程 | **21** |
| `switch` 模式匹配 | **21** |
| `SequencedCollection` | **21** |
| 未命名变量 & 模式 `_` | **25**（22 转正） |
| Markdown Javadoc | **25**（23 转正） |
| Stream Gatherers | **25**（24 转正） |
| 虚拟线程不再被 synchronized 钉住 | **25**（24 转正） |
| Flexible Constructor Bodies | **25** |
| Scoped Values | **25** |

> 门控不满足时的降级写法（JDK 8 等价）：`var x` → 显式类型；`record Point(...)` → final 类 + 全参构造 + getter；文本块 → 普通字符串（转义）；`switch` 表达式 → 传统 `switch` 语句 + break。

## 反例详解（antipattern）

### 1. 虚拟线程 + synchronized 的 LTS 版本陷阱（JDK 21 vs 25）
```java
// JDK 21 LTS：虚拟线程遇到 synchronized 会被钉住载体线程（pin），失去并发优势
// 旧建议：JDK 21 虚拟线程代码中禁用 synchronized，改用 ReentrantLock
public void fetch() {
    synchronized (this) {   // ✗ JDK 21：pin 住载体线程
        doBlockingIO();
    }
}

// JDK 25 LTS（吸收 JEP 491）：synchronized 不再 pin 虚拟线程，可直接使用
public void fetch() {
    synchronized (this) {   // ✓ JDK 25：不再 pin，无需改 ReentrantLock
        doBlockingIO();
    }
}
```
> 不一刀切：JDK 21 虚拟线程避免 synchronized（改 `ReentrantLock`），JDK 25 不再 pin 可直接用——按目标 LTS 版本判断。

### 2. Flexible Constructor Bodies 误用（JDK 25+）
```java
// ✗ 在 super() 前做可观测副作用（构造未完成即暴露 this）
public class Child extends Parent {
    public Child(int x) {
        this.registry = EventBus.register(this);  // this 未完全构造！
        super(x);
    }
}

// ✓ 仅用于参数校验 / 防御性拷贝（无副作用、不暴露 this）
public class Child extends Parent {
    public Child(int x) {
        if (x < 0) throw new IllegalArgumentException("x must be >= 0");
        super(x);  // 校验后再调用
    }
}
```
> Flexible Constructor Bodies（JEP 513）允许 super()/this() 前执行语句，但**仅限无副作用的准备逻辑**（参数校验、防御性拷贝、字段计算）。禁止在 super() 前暴露 `this` 或触发可观测副作用——此时对象尚未完全构造。

### 3. sun.misc.Unsafe / Security Manager 依赖（JDK 25 移除）
```java
// ✗ 依赖 Unsafe 内存操作
sun.misc.Unsafe unsafe = ...;
unsafe.putLong(address, value);   // JDK 25 已移除

// ✗ 依赖 Security Manager
System.setSecurityManager(new MySecurityManager());  // JDK 25 已永久禁用

// ✓ 迁移至官方 API
// 内存操作 → Foreign Function & Memory API（JEP 454，JDK 25 转正）
// 安全管理 → 应用级沙箱（容器/OS 级隔离），不再依赖 JVM Security Manager
```
> JDK 25 LTS 永久移除 Security Manager（JEP 486）并废弃 `sun.misc.Unsafe` 内存方法（JEP 471/498）。依赖这些内部 API 的代码将无法运行。迁移到 FFM API（`java.lang.foreign`）替代 Unsafe 内存操作；用容器/OS 级隔离替代 Security Manager。

## JDK 25 新特性示例

> JDK 8–21 的语法（var/switch 表达式/文本块/record/instanceof/sealed/虚拟线程/switch 模式匹配）为通用语法，按门控表使用；虚拟线程与 Scoped Values 详见 `05-concurrency.md`。

### 未命名变量 `_`（忽略值时用）
```java
// ✓ 用 _ 显式标记忽略值，消除未使用变量警告
try (var conn = dataSource.getConnection()) {
    var _ = conn.getAutoCommit();  // 明确表示不关心返回值
}
// catch 也可用 _ 忽略异常变量
try { ... } catch (TimeoutException _) { log.warn("timeout, ignore"); }
```

### Stream Gatherers（自定义中间操作）
```java
// Stream Gatherers 补充 Collectors 能力，支持自定义中间操作
// 例：固定窗口分组（每 3 个元素一组）
List<List<Integer>> windows = numbers.stream()
    .gather(Gatherers.windowFixed(3))
    .toList();
// 更多自定义 Gatherer 见 java.util.stream.Gatherer
```
