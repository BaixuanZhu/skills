# 01 · 静默陷阱的推理与验证

收录标准：**写错后测试是绿的**。会让测试变红的（`verify` 默认恰好 1 次、严格桩模式的多余 stub、JUnit 4/5 混用）不收录——当场暴露，agent 自己会改。

这里只写「为什么绿」和「怎么确认自己不是假绿」。改法三行能写完，不贴完整实现。

## 一、金额用 `equals`

`assertEquals(new BigDecimal("90.00"), actual)`：actual 是 `90` 红，是 `90.000` 也红，报错信息写「expected: 90.00 but was: 90」，看不出是 scale 问题，容易被改成 `new BigDecimal("90")` 蒙过去。

scale 恰好一致时它是绿的——而真正要保证的是「金额固定两位小数」，这个要求被掩盖了。实现里某条分支少写一次 `setScale(2)`，测试照样绿。

改法：`isEqualByComparingTo("90.00")` 比值；要校小数位就单独断 `scale()`。

## 二、被测类内部 `new` 的依赖

被测代码里 `PaymentClient client = new PaymentClient();` —— 测试里 mock 不到它。测试把 mock 注入到别处（或干脆没注入），被测代码安静地用自己造的实例，断言对着一个假对象跑，全程无报错。

判别：`when(...)` 的桩值没生效、`verify` 从不命中，但断言全过——先查被测类有没有 `new`。

改法：构造器注入。改不动说明这个类不可测，先拆。

## 三、对 `spy` 用 `when()`

`when(real.size()).thenReturn(10)` 会**先执行** `real.size()`，拿到结果再替换成桩值——真实方法的副作用已经发生了。

真实方法多半不出错，只是被多调一次，所以是绿的。等它有副作用（计数、写库、抛异常）时，失败点出现在毫不相干的断言上。

规则：stub `spy` 或会抛异常的方法，一律 `doReturn(10).when(spy).size()` / `doThrow(...).when(obj).method()`。

## 四、`any()` 放过参数构造

`when(mapper.selectOne(any()))` 只 stub 返回值。被测代码构造的 wrapper 是它的**参数**，不是外部依赖——`.eq(User::getId, name)` 本该是 `getName`，写错也不报。

不要 mock wrapper 本身（重建不出同一实例）。需要校条件时 `ArgumentCaptor` 捕获再 `verify`。

## 五、`mockStatic` 不释放

`mockStatic(X.class)` 不包 try 就泄漏到同线程后续测试。之后所有测试看到的都是被 stub 的静态方法，失败点漂移到别的类，排查成本远高于写 try。

## 六、异常断言断在根父类

`assertThrows(RuntimeException.class, ...)`：任何异常都满足，被测代码抛 NPE 也算通过。

改法：`assertThatThrownBy(...).isInstanceOf(IllegalArgumentException.class).hasMessage("数量必须大于 0")`。

## 七、没有断言

调一下方法、不抛异常就算「覆盖」——全绿，什么也没验。只验证「不抛异常」时，明确写 `assertThatCode(...).doesNotThrowAnyException()`，让意图显式。

## 八、把轻量装配当成纯单测

`@TestConfiguration` + `@Import` + `@Autowired` 起的仍是 Spring 上下文（不是全量，但也不是无）。允许，条件是上下文里**只有 mock 与纯内存对象**——不出现真实 `DataSource`、中间件客户端，不拉 `@SpringBootApplication` 扫描。出现这些就跨到集成测试。
