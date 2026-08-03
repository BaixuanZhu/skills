# 11 条 test-prompt（v1.4.0 达尔文验证：回归 + 对抗）

> 盲评 agent 假设自己是"接到这个用户请求的 coding agent，手里只有这套技能"，判断能否给出合格回答。
>
> **T1-T8 = 回归集**（复用 v1.3.1 验证的 8 条，验证 v1.4.0 三处改动没让原有场景退步）。
> **T9-T11 = 对抗集**（本次新增，直击三条反馈的根本原因；每条在 v1.3.2 与 v1.4.0 间存在可判别的行为差异）。

---

## T1 — JaCoCo 集成
```
我在写一个 Spring Boot 项目，想给单元测试加覆盖率工具，帮我看怎么接入。
```

## T2 — 遗留代码补测
```
我接手了一个五年前的 Java 项目，有个 Service 类 400 行，里面全是 static 调用和 new 出来的依赖，
现在要给它补单元测试。我该怎么开始？
```

## T3 — review checklist
```
我刚写完一批单元测试，提交前想自查质量。有没有一份测试代码的 review 清单？
```

## T4 — 快速入门
```
我第一次接触单元测试规范，这个技能文件很多，我该从哪开始看？
```

## T5 — ArchUnit 跨层
```
我有个 Controller 直接调了 Repository，绕过了 Service 层。
怎么用测试或工具防止这种跨层违规？
```

## T6 — 停止信号可执行性（回归重点：05 刚被精简）
```
我设计完用例了，按规范说要看"三个停止信号"判断够不够。
这三个信号具体怎么操作检查？我跑完测试后该看什么？
```

## T7 — AI 生成测试自欺
```
用 AI 一次性给我生成了一批单元测试，看起来四维度都覆盖了。
我直接用这批测试可以吗？有没有风险要注意？
```

## T8 — Mock 复杂场景
```
我要测一个 Service，它内部调用了 MyBatis-Plus 的链式查询 lambdaQuery().eq().one()，
还有个工具类的静态方法。这种复杂场景 Mock 怎么写？给个范例。
```

---

## T9 — 【对抗 · 反馈1 根因】表格型 VO 逐列断言 + 集合断言
```
我有个 Excel 导出 VO，16 列（姓名/手机号/身份证号/部门/入职日期/岗位/职级/...）。
我要测一个 toExportVO(source) 方法，它把 DB 实体转成这个 16 列 VO。

问题：
(a) 这 16 列的字段映射，断言该怎么写？同事说用 AssertJ 的 extracting(...).containsExactly()
    一次性断言更"专业"，但我不确定。
(b) 另外这个方法还会返回一个 List<OrderExportVO>，我要校验 list 的元素个数和顺序，
    这部分该用什么断言？

我两个场景都希望断言失败时能快速定位是哪个字段/哪个元素出了问题。
```

## T10 — 【对抗 · 反馈2 根因】项目既定 mock 装配 vs @MockBean 滥用
```
我项目里测试是这样装配的（团队 spec 规定的，所有单测都走这个 TestConfig）：

  @Configuration
  class TestMockConfig {
      @Bean OrderRepository orderRepository() { return Mockito.mock(OrderRepository.class); }
      @Bean PaymentClient paymentClient() { return Mockito.mock(PaymentClient.class); }
  }

  @ExtendWith(SpringExtension.class)
  @Import(TestMockConfig.class)
  class OrderServiceTest {
      @Autowired OrderService service;   // 注入真实 OrderService，依赖是 TestConfig 里的 mock
      @Autowired OrderRepository orderRepository;

      @Test void should_xxx() { ... }
  }

问题：
(a) 有个同事 review 说我们这种写法"违反了单测规范，应该用 @Mock + @InjectMocks"，
    说 @MockBean 思路是反模式。他说的对吗？我该怎么回应？
(b) 但我们隔壁组确实有人图省事，直接在纯单测里用 @MockBean 起整个 Spring 上下文
    （@SpringBootTest + @MockBean），那是不是真有问题？
```

## T11 — 【对抗 · 反馈3 根因】DoD 写"覆盖率 ≥ 80%"
```
我们团队在推单元测试规范，现在 DoD（Definition of Done）里有一条：
"单元测试覆盖率不低于 80% 才算这个任务完成"。

我作为 QA 觉得这条有点问题但说不太清。你帮我看看这条 DoD 合不合理？
如果改，应该改成什么？我们希望能被 PR 模板 / 提交前 checklist 直接引用。
```
