# 11 条 test-prompt（v1.5.0 回归验证：回归 + 对抗）

> 盲评 agent 假设自己是"接到这个用户请求的 coding agent，手里只有这套技能"，判断能否给出合格回答。
>
> **R1-R7 = 回归集**（验证 v1.5.0 五处改动——description 重写 / 06 重组 / 覆盖率立场 / guide-pro 清零 / DoD 口径统一——没让原有场景退步）。
> **A1-A4 = 对抗集**（直击本轮五处改动的根本原因；每条在 v1.4.1 与 v1.5.0 间存在可判别的行为差异）。

---

## R1 — JaCoCo 集成（用户主动问；盯 05 接入节改写）
```
我在写一个 Spring Boot 项目，想给单元测试加覆盖率工具，帮我看怎么接入。
```

## R2 — 遗留代码补测（盯 05 遗留段 + guide-pro 指针删除）
```
我接手了一个五年前的 Java 项目，有个 Service 类 400 行，里面全是 static 调用和 new 出来的依赖，
现在要给它补单元测试。我该怎么开始？
```

## R3 — review checklist / DoD 引用（盯 DoD 第二条重写）
```
我刚写完一批单元测试，提交前想自查质量。有没有一份测试代码的 review 清单？
最好是我跑完测试后能逐项核对的那种，特别是"分支都测到了没"这项怎么检查。
```

## R4 — 栈基线导航（盯 06 结构重排：版本知识三处散布 → §1 决策表）
```
我要开始给项目写单测了，先帮我定工具基线：普通 Maven 工程（非 Spring Boot），
pom 里已有 junit-jupiter 和 mockito-core 4.11.0。
我该确认哪些版本差异？mockStatic 能不能直接用？
```

## R5 — JUnit 4 遗留项目写法（盯 JUnit 4 差异表移位 §4 → §1）
```
我们项目还在用 JUnit 4（pom 里是 junit:junit:4.13.2，测试类用 @RunWith）。
我新写的测试要注意什么？和 JUnit 5 有什么写法差异？
```

## R6 — Mock 复杂场景（盯 06 §3 内容保留完整性）
```
我要测一个 Service，它内部调用了 MyBatis-Plus 的链式查询 lambdaQuery().eq().one()，
还有个工具类的静态方法。这种复杂场景 Mock 怎么写？给个范例。
```

## R7 — mockStatic 注意事项（盯 §3.4 两节合并重排 + 版本坑移 §1）
```
我需要 mock 一个静态方法（工具类 IdUtil.getId()），第一次用 mockStatic。
用的时候有什么要注意的？比如怎么不污染其他测试？
```

---

## A1 — 【对抗 · 覆盖率立场】80% 门禁配合 + 无工具分支核对
```
两个问题：
(a) 我们 CI 上有条老门禁：单元测试行覆盖率 ≥ 80% 才能合并。我不想动这条门禁，
    但我担心大家为了过门禁写凑数测试。我该怎么配合这条门禁把单测写好？
(b) 我本地项目没接 JaCoCo，也不想往 pom 里加新插件，但我提交前想知道
    被方法的分支是不是都测到了，有什么办法？
```

## A2 — 【对抗 · 坐标断链修复】非 Spring 项目引 AssertJ
```
非 Spring 的普通 Maven 项目。我测一个坐标转换方法，要对返回对象的 x/y/z 三个字段
做整体断言，按规范这属于"字段分组断言"该用 AssertJ 的 extracting。
我项目里还没引 AssertJ，给我要加的依赖坐标。
```

## A3 — 【对抗 · 跨插件断链修复】祖传大方法重构第一步
```
我有个 500 行的订单折扣计算方法，圈复杂度估计 40+，一直是没人敢动的祖传代码，零测试。
我想重构它但怕改坏。第一步该干什么？有没有判断"这方法复杂到必须先锁行为"的标准？
```

## A4 — 【对抗 · description 触发令牌】贴代码求 review（不提框架名）
```
帮我 review 这段测试写得对不对：

@ExtendWith(MockitoExtension.class)
class DiscountServiceTest {
    @Mock CouponClient couponClient;
    @InjectMocks DiscountService service;

    @ParameterizedTest
    @MethodSource("cases")
    void should_calc_when_input(Case c) {
        when(couponClient.fetch(anyString())).thenReturn(c.coupon);
        assertEquals(c.expected, service.calc(c.input));
    }
}
```
