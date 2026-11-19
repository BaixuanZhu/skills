# T1 — MemberIndex 实现（三组同一任务书）

项目 JDK 17（`maven.compiler.release=17`），Maven 工程。`Member` 类已给定
（`src/main/java/com/example/directory/Member.java`）。

实现 `com.example.directory.MemberIndex`，文件放
`src/main/java/com/example/directory/MemberIndex.java`，提供四个能力
（**方法名固定，返回类型与 static/实例自定**）：

- `index(List<Member> members)` —— 按 id 建索引
- `find(List<Member> members, String id)` —— 查单个成员
- `averageAge(List<Member> members)` —— 平均年龄
- `groupByTeam(List<Member> members)` —— 按 team 分组

输入来自外部导入，质量不可信：集合里可能有 `null` 元素、可能有重复 id 的成员、
可能整个集合为空；参数本身也可能收到 `null`；成员的 `age` 字段可能没有值。

要求：

1. 写完后编译通过（`mvn -q compile`）。
2. 在 `response.md` 里说明你的边界处理决策：每类情况按什么规则、为什么；以及编译/验证情况。
3. 只创建/修改 `src/main/java/com/example/directory/MemberIndex.java` 与 `response.md`；
   不得修改 `pom.xml` 与 `Member.java`。
4. 只使用当前工作目录内的文件，不读取目录之外的任何文件，不联网。
