# 02 · 集合

## 选型

| 需求 | 选 | 不要用 |
|---|---|---|
| 默认列表 | `ArrayList` | `LinkedList`（除频繁头插/当队列） |
| 默认 Map | `HashMap` | `Hashtable`（全表锁） |
| 保持插入顺序 | `LinkedHashMap` / `LinkedHashSet` | `HashMap` + 额外排序 |
| 按 key 排序 / 范围查询 | `TreeMap` / `TreeSet` | 取出后排序 |
| 高频查存在 | `HashSet` | `ArrayList.contains`（O(n)） |
| 栈 / 队列 / 双端 | `ArrayDeque` | `Stack`（同步、已不推荐）、`LinkedList` |
| 并发读多写少 | `ConcurrentHashMap` | `Collections.synchronizedMap` |
| 固定元素个数的只读集合 | `List.of` / `Set.of` / `Map.of` | `Arrays.asList` |

`Map.of` 最多 10 对，超过用 `Map.ofEntries(Map.entry(k, v), ...)`。

## 初始化

| ✗ | ✓ |
|---|---|
| `List<String> l = new ArrayList<>(); l.add(a); l.add(b);` | `List.of(a, b)`（不可变） |
| `List<String> l = Arrays.asList(a, b);` 后想 `add` | `new ArrayList<>(List.of(a, b))` |
| `Map<String, Integer> m = new HashMap<>(); m.put(a, 1); m.put(b, 2);` | `Map.of(a, 1, b, 2)`；需可变 `new HashMap<>(Map.of(...))` |
| `Collections.singletonList(x)` | `List.of(x)`（9+） |
| `new HashSet<>(Arrays.asList(a, b))` | `Set.of(a, b)` |

## 不可变：三种语义不同

| 写法 | 语义 | 何时用 |
|---|---|---|
| `List.of(...)` / `Set.of(...)` | 新建不可变集合，**调用返回的集合是独立副本** | 常量、方法返回、防御性拷贝 |
| `List.copyOf(other)` | 拷贝成不可变集合；`other` 已不可变时**可能直接返回它** | 返回前防御性拷贝（10+） |
| `Collections.unmodifiableList(other)` | **只是视图**，原集合改动会透出来 | 极少；不确定时改用 `copyOf` |

## Map 增改（一次原子操作，替代两段式）

| ✗ 两段式 | ✓ |
|---|---|
| `if (!m.containsKey(k)) m.put(k, new ArrayList<>()); return m.get(k);` | `m.computeIfAbsent(k, x -> new ArrayList<>())` |
| `Integer v = m.get(k); if (v == null) m.put(k, 1); else m.put(k, v + 1);` | `m.merge(k, 1, Integer::sum)` |
| `if (m.get(k) == null) m.put(k, v);` | `m.putIfAbsent(k, v)` |
| `if (m.containsKey(k)) m.put(k, m.get(k) + 1);` | `m.computeIfPresent(k, (key, v) -> v + 1)` |
| `m.put(k, m.getOrDefault(k, 0) + 1)` 单线程可用 | 并发下用 `m.merge(k, 1, Integer::sum)` |

`computeIfAbsent` 的映射函数**不要修改同一个 map**（会抛 `ConcurrentModificationException`），也不要返回 null（不会写入，且无提示）。

## 遍历中修改

| ✗ | ✓ |
|---|---|
| `for (X x : list) { if (p(x)) list.remove(x); }` | `list.removeIf(this::p)` |
| 迭代器 + `iterator.remove()` | 同上；需要遍历中做别的操作才用迭代器 |
| `for (K k : map.keySet()) map.remove(k)` | `map.entrySet().removeIf(e -> p(e))` |

## 比较器

| ✗ | ✓ |
|---|---|
| `(a, b) -> a.getAge() - b.getAge()` | `Comparator.comparingInt(Foo::getAge)` |
| 手写多字段 if-else | `comparing(Foo::getName).thenComparingInt(Foo::getAge)` |
| 不处理 null | `Comparator.nullsLast(comparing(Foo::getName))` / `nullsFirst` |
| `list.sort((a, b) -> b.getX().compareTo(a.getX()))` | `comparing(Foo::getX).reversed()` |
| `x.compareTo(y)` 可能 null | `Comparator.naturalOrder()` 配合 `nullsFirst` |

减法比较器有 **int 溢出**风险（`a - b` 超出 int 范围时符号翻转），一律用 `comparingInt` / `Integer.compare`。

## 坑

- **`subList` 是视图**：`list.subList(0, 3)` 返回的是原列表的窗口，对它的修改会写回原列表，原列表结构性修改会让它抛 `ConcurrentModificationException`。需要独立列表就 `new ArrayList<>(sub)` / `List.copyOf(sub)`。
- **`Arrays.asList` 定长**：`add` / `remove` 抛 `UnsupportedOperationException`（`set` 可以，因为写回原数组）。
- **`Arrays.asList(基本类型数组)`**：`Arrays.asList(new int[]{1,2})` 得到 `List<int[]>`，只有 1 个元素。要 `Arrays.stream(arr).boxed().toList()`。
- **`List.of` 拒 null**：`List.of(a, null)` 抛 NPE；`Arrays.asList` 允许 null。
- **`List.of` 结果不可变**：`List.of(1,2).add(3)` 抛 `UnsupportedOperationException`。
- **`Map.of` 拒 null value**：`Map.of(k, null)` 抛 NPE，`HashMap` 允许。
- **返回内部集合**：`public List<X> getItems() { return items; }` 调用方 `clear()` 就改了内部状态 → `List.copyOf(items)`。
- **`hashCode`/`equals` 依赖可变字段**：先把对象放进 `HashSet` 再改字段，就再也查不到它。
- **`ConcurrentHashMap` 不允许 null key/value**：`get` 返回 null 无法区分「没有」和「值是 null」。
- **集合判空**：`c.isEmpty()` 前仍需 `c != null`，除非调用方保证非空（`requireNonNull` 或在方法签名上约定）。
