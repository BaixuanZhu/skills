# 01 · 静默陷阱（写错不报警，测试仍然绿）

收录标准：**写错后测试是绿的**。会让测试变红的（`verify` 默认恰好 1 次、严格桩模式的多余 stub、JUnit 4/5 混用）不收录——那些当场就暴露，agent 自己会改。

## 一、金额用 `equals` 比较

```java
// ✗ scale 一起比
assertEquals(new BigDecimal("90.00"), actual);   // actual 是 90 → 红；是 90.000 → 也红
// 红的时候报 "expected: 90.00 but was: 90"，看不出是 scale 问题，容易被改成 new BigDecimal("90") 蒙过去

// ✓ 只比值
assertThat(actual).isEqualByComparingTo("90.00");
```

**为什么绿着也要改**：真正要断的是「金额固定两位小数」。`equals` 在 scale 恰好一致时通过，把这个要求掩盖了；实现里某条分支少写一次 `setScale(2)`，测试照样绿。需要校小数位就单独断 `assertThat(actual.scale()).isEqualTo(2)`。

## 二、被测类内部 `new` 的依赖

```java
// ✗ 被测对象自己造依赖
class BadService {
    public void pay() {
        PaymentClient client = new PaymentClient();   // 测试里 mock 不到它
        client.pay();
    }
}

// ✓ 构造器注入
class GoodService {
    private final PaymentClient client;
    GoodService(PaymentClient client) { this.client = client; }
}
```

**为什么绿**：测试把 mock 注入到别处（或干脆没注入），被测代码安静地用自己 `new` 的实例。断言对着一个假对象跑，全程无报错。

判别：测试里 `when(...)` 的桩值没有生效、`verify` 从不命中，但断言全过——先查被测类有没有 `new`。

同类：`LocalDate.now()` / `UUID.randomUUID()` / `new ObjectMapper()`。调用点在你自己代码里就不算「够不着」——注入 `Clock.fixed(...)` 或 `IdGenerator` 接口，不要上 `mockStatic`。

## 三、对 `spy` 用 `when()`

```java
List<String> real = spy(new ArrayList<>());

// ✗ when() 先执行真实方法，再把结果替换成桩值——副作用已经发生
when(real.size()).thenReturn(10);

// ✓ doReturn 先行，跳过真实方法
doReturn(10).when(real).size();
```

**为什么绿**：真实方法多半不出错，只是被多调了一次。等真实方法有副作用（计数、写库、抛异常）时，失败点会出现在毫不相干的断言上。

规则：**stub `spy` 或会抛异常的方法，一律 `doReturn/doThrow().when(obj)`**。

## 四、`any()` 放过了参数构造

```java
// 被测：service.findActive(name) 内部 new LambdaQueryWrapper().eq(User::getName, name) 再 selectOne
// ✗ 只 stub mapper 返回，wrapper 写成 .eq(User::getId, name) 也不报
when(mapper.selectOne(any())).thenReturn(null);

// ✓ 需要校条件时捕获
ArgumentCaptor<LambdaQueryWrapper<User>> captor = ArgumentCaptor.forClass(LambdaQueryWrapper.class);
verify(mapper).selectOne(captor.capture());
```

wrapper 是被测代码构造的**参数**，不是外部依赖——不要去 mock wrapper 本身（重建不出同一实例）。但 `any()` 会让「查询条件写错字段」这类 bug 静默通过。

## 五、`mockStatic` 不释放

```java
// ✗ 静态 mock 泄漏到同线程后续测试
MockedStatic<IdUtil> m = mockStatic(IdUtil.class);

// ✓
try (MockedStatic<IdUtil> m = mockStatic(IdUtil.class)) {
    m.when(IdUtil::getId).thenReturn("FAKE_ID");
}
```

**为什么危险**：泄漏后，后面所有同类测试看到的是被 stub 的静态方法，失败点漂移到别的类，排查成本远高于写 try。

## 六、异常断言断在根父类

```java
// ✗ 抛 NPE 也算通过
assertThrows(RuntimeException.class, () -> service.create(req));

// ✓
assertThatThrownBy(() -> service.create(req))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessage("数量必须大于 0");
```

## 七、没有断言

调一下方法、不抛异常就算「覆盖」——测试全绿，什么也没验。每个测试至少一条行为断言；只验证「不抛异常」时，明确写 `assertThatCode(...).doesNotThrowAnyException()`，让意图显式。

## 八、把轻量装配当成纯单测

`@TestConfiguration` + `@Import` + `@Autowired` 起的仍是 Spring 上下文（不是全量，但也不是无）。允许，条件是上下文里**只有 mock 与纯内存对象**——不出现真实 `DataSource`、中间件客户端，不拉 `@SpringBootApplication` 扫描。出现这些就跨到集成测试，改用 `@SpringBootTest` 并把测试放到 java-integration-test 的范围里。
