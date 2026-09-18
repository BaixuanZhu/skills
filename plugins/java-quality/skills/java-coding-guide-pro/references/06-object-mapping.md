# 06 · 对象映射与 Bean 处理

> **栈适配**：推荐构件仅在项目无既有方案时采用，否则跟随既有栈——**但「禁反射/序列化拷贝」为硬约束，不因既有栈豁免**。

> **Bean 拷贝/映射只有两条正路：① MapStruct（编译期生成，类型安全）② 显式 setter / 构造器（字段少时）。禁止一切运行时反射/序列化拷贝**——`BeanUtils.copyProperties`、`BeanUtil.copyProperties`/`toBean`/`mapToBean`/`beanToMap`、`ObjectUtil.cloneByStream`：按字符串字段名对齐或强转，字段名拼错、类型不符只在运行期暴露（静默 null 或 `ClassCastException`），编译器与审稿都发现不了。无 annotation processor 时也只用显式 setter/构造器。
> **对象工具**：`ObjectUtil`（`cn.hutool.core.util`）。

## 规范速查

| 场景 | ✗ 禁止 | ✓ 推荐 |
|---|---|---|
| 属性拷贝（**默认**） | 反射拷贝：`BeanUtils.copyProperties`、`BeanUtil.copyProperties` | **MapStruct**（编译期生成）/ 字段少时显式 setter 或构造器 |
| 拷贝到新对象 | `BeanUtil.copyProperties(src, Cls.class)`、`toBean` 等反射 | `new Target(src.getA(), src.getB())` 构造器 / MapStruct |
| 拷贝到已有对象（忽略 null） | 反射 + `CopyOptions.ignoreNullValue()` | 显式 setter 带 `if (src.getXxx() != null)` / MapStruct |
| 转 Map | `BeanUtil.beanToMap`（反射读字段） | 显式 `map.put("k", bean.getXxx())` / MapStruct Bean→Map |
| Map 转 Bean | `BeanUtil.toBean` / `mapToBean`（反射） | 优先免 Map 中转：Jackson `readValue(json, Cls.class)` / `@RequestBody Cls dto`；确需则 MapStruct 从 Map 映射 / 显式构造器 |
| 相等（防 NPE） | `a.equals(b)` | `ObjectUtil.equal(a, b)` |
| 默认值 | `obj != null ? obj : def` | `ObjectUtil.defaultIfNull(obj, def)` |
| 判空 | `obj == null` | `ObjectUtil.isNull(obj)` / `isNotNull` |
| 深拷贝 | 手搓 Cloneable / `ObjectUtil.cloneByStream`（序列化强转，类型/字段错运行期才暴露） | 显式拷贝构造器（逐字段 `new`） / MapStruct |
| toString | 手写/`ToStringBuilder`/`Validate`（commons-lang3） | Lombok `@ToString` / `@Data`（Hutool + Lombok 已覆盖，不引 commons-lang3） |

## 反例详解（antipattern）

### 1. 反射拷贝是黑盒，AI 时代禁止
```java
// ✗ Spring 版顺序 (source, target)，Apache 版完全相反 (dest, source)——混用即使不报错也静默拷空
BeanUtils.copyProperties(target, source);

// ✗ Hutool BeanUtil.copyProperties 同样是反射：字段名拼错/类型不符只在运行期暴露
BeanUtil.copyProperties(source, target);
UserDTO dto = BeanUtil.copyProperties(user, UserDTO.class);

// ✓ 默认 MapStruct（编译期类型安全，字段名/类型不符编译即报错）
@Mapper
public interface UserMapper {
    UserMapper INSTANCE = Mappers.getMapper(UserMapper.class);
    UserDTO toDto(User user);
}
// 使用：UserDTO dto = UserMapper.INSTANCE.toDto(user);

// ✓ 字段少时直接显式构造器 / setter（编译期类型安全）
UserDTO dto = new UserDTO(user.getName(), user.getAge());
```

### 2. Map ↔ Bean 禁止反射
```java
// ✗ 字段名靠字符串对齐，拼错/类型错只在运行期暴露（静默 null 或 ClassCastException）
User u = BeanUtil.toBean(m, User.class);
Map<String, Object> m = BeanUtil.beanToMap(user, true, true);

// ✓ 优先免 Map 中转：JSON 直接反序列化到类型化 DTO
UserDTO dto = objectMapper.readValue(json, UserDTO.class);

// ✓ 确需 Map→Bean：MapStruct 从 Map 映射（编译期生成）
@Mapper
public interface UserMapper {
    UserMapper INSTANCE = Mappers.getMapper(UserMapper.class);
    @Mapping(target = "name", source = "customerName") // source 即 map key
    User toUser(Map<String, Object> map);
}

// ✓ Bean→Map：显式提取（编译期类型安全）
Map<String, Object> m = new HashMap<>();
m.put("name", user.getName());
m.put("age", user.getAge());
```

### 3. `@ToString` 循环引用
```java
// ✗ 父子互引时 toString 栈溢出
@ToString class Dept { List<User> users; }
@ToString class User { Dept dept; }

// ✓ 断开循环
@ToString(exclude = "users") class Dept { List<User> users; }
```

### 4. `equals` 可能 NPE
```java
// ✗ a 为 null 抛 NPE
if (a.equals(b)) { ... }

// ✓ ObjectUtil.equal（equal 是原始名；equals 是 5.4.3+ 别名，两者等价）
if (ObjectUtil.equal(a, b)) { ... }
```

## MapStruct 完整示例（推荐）

```java
// 1. 定义 Mapper 接口
@Mapper
public interface OrderMapper {
    OrderMapper INSTANCE = Mappers.getMapper(OrderMapper.class);

    OrderDTO toDto(Order order);

    @Mapping(target = "amountStr", source = "amount")  // 不同名字段映射
    @Mapping(target = "internal", ignore = true)        // 忽略目标字段
    OrderDetailDTO toDetail(Order order);

    List<OrderDTO> toDtoList(List<Order> orders);       // 集合映射自动支持
}
```

MapStruct 坐标与 annotation processor 配置见 SKILL.md「C-CHECK 询问（仅高风险能力缺失时触发）」（编译期，零运行时依赖；JDK 8 兼容）。
