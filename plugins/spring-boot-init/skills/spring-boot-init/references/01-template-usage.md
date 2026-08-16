# 01 · 模板使用（assets/maven-multimodule 机械用法）

本文是 `assets/maven-multimodule/` 的唯一使用说明：结构、占位符、机械步骤、单模块形态、增删模块、自检。命令均为 Git Bash。

## 模板结构

```
assets/maven-multimodule/
├── pom.xml                        # 聚合根：packaging=pom + <modules> + 插件/依赖版本收敛
├── .gitignore                     # target/、IDE 文件
├── sample-core/
│   └── pom.xml                    # 基础库模块（普通 jar，无 repackage）
└── sample-app/                    # 可执行模块（spring-boot-maven-plugin repackage）
    ├── pom.xml                    # 依赖 sample-core + web + test
    └── src/
        ├── main/java/com/example/Application.java   # 主类（挪到 groupId 路径）
        └── main/resources/application.yml
```

根 pom 已收敛：`dependencyManagement`（spring-boot-dependencies BOM `{{BOOT_VERSION}}` + `{{GROUP_ID}}:sample-core` 模块间依赖）+ `pluginManagement`（compiler 显式 `release` / surefire / spring-boot / resources / spotless，版本全在 `<properties>`）+ 公共依赖 lombok（optional）。**子模块因此一律不带版本号。**

## 占位符（5 个，只出现在 pom.xml 与 application.yml 文本中）

| 占位符 | 含义 | 示例值 |
|---|---|---|
| `{{GROUP_ID}}` | groupId，同时决定 Java 包路径 | `com.acme.order` |
| `{{ARTIFACT_ID}}` | 根 artifactId（项目名）+ `spring.application.name` | `order-service` |
| `{{VERSION}}` | 项目版本 | `1.0.0-SNAPSHOT` |
| `{{JAVA_VERSION}}` | JDK 版本（compiler `release`） | `21` |
| `{{BOOT_VERSION}}` | Spring Boot 版本（BOM import） | `3.5.4` |

## 机械步骤（整体初始化）

```bash
# 1. 复制模板到目标目录
cp -r <技能目录>/assets/maven-multimodule/. /path/to/order-service/
cd /path/to/order-service

# 2. 替换占位符（以 com.acme.order / order-service / JDK 21 / Boot 3.5.x 为例）
#    含占位符的文件固定 4 个，显式列出——Git Bash 下 grep|xargs 管道会丢文件名路径分隔符，勿用
sed -i \
    -e 's/{{GROUP_ID}}/com.acme.order/g' \
    -e 's/{{ARTIFACT_ID}}/order-service/g' \
    -e 's/{{VERSION}}/1.0.0-SNAPSHOT/g' \
    -e 's/{{JAVA_VERSION}}/21/g' \
    -e 's/{{BOOT_VERSION}}/3.5.4/g' \
    pom.xml sample-core/pom.xml sample-app/pom.xml sample-app/src/main/resources/application.yml

# 3. 挪包目录并改 package 行（com/example → groupId 路径）
cd sample-app/src/main/java
mkdir -p com/acme/order
mv com/example/Application.java com/acme/order/
sed -i 's/^package com\.example;/package com.acme.order;/' com/acme/order/Application.java
cd -

# 4. 重命名样板模块为业务模块名（多模块形态；单模块形态见下节）
mv sample-core order-core
mv sample-app  order-app
sed -i 's/sample-core/order-core/g; s/sample-app/order-app/g' pom.xml order-core/pom.xml order-app/pom.xml

# 5. 自检（必须全过）
grep -rn '{{' .            # 无输出
grep -rn 'com\.example' .  # 无输出
mvn -q validate            # BUILD SUCCESS（Windows Git Bash 用 mvn.cmd，输出重定向到日志再读）
```

步骤 4 的 sed 同时改掉根 `<modules>`、根 `dependencyManagement` 的模块坐标、app 模块的 `<parent>` 外依赖坐标——三处引用与目录名一次对齐。

## 单模块形态（只留一个可执行模块）

```bash
rm -rf sample-core
```

再手动删三处引用：①根 pom `<modules>` 的 `<module>sample-core</module>` 行；②根 pom `dependencyManagement` 的 `{{GROUP_ID}}:sample-core` 条目；③sample-app pom 里对 `sample-core` 的 `<dependency>`。然后照常执行步骤 2~5（步骤 4 只重命名 sample-app）。

## 增删模块（已有工程加子模块同此法）

- **增库模块**：`cp -r sample-core <新名>` → 改其 pom 的 `<artifactId>`/`<name>` → 根 `<modules>` 加行 → 需要被其他模块依赖时，根 `dependencyManagement` 加 `{{GROUP_ID}}:<新名>` 条目。
- **增可执行模块**：`cp -r sample-app <新名>` → 同上三步（自带 repackage 与主类，记得把包目录与主类也挪到对应路径）。
- **删模块**：`rm -rf <目录>` + 根 `<modules>` 去行 + 其他模块对它的 `<dependency>` 删除。

## ✗ 禁止 → ✓ 推荐

| ✗ 禁止 | ✓ 推荐 |
|---|---|
| 从零手写 pom / 目录 / 主类 | 一律 `cp` 模板 + 替换占位符 |
| 替换后残留 `{{...}}` | `grep -rn '{{'` 零残留才算完成 |
| `<modules>` 与目录名不一致 | 增删 / 重命名后同步根 pom `<modules>`（用步骤 4 的 sed 一次对齐） |
| 库模块（如 core）启用 spring-boot repackage | repackage 只在可执行 app 模块；库模块保持普通 jar |
| 子模块依赖写 `<version>` | 版本一律由根 `dependencyManagement` / BOM 收敛 |
| 需要资源过滤时直接开 filtering 用 `${...}` | 先配 `@..@` 分隔符（`${}` 与 Spring 占位符冲突）；模板默认不开过滤 |
| 改根 GAV 后子模块 `<parent>` 不同步 | 根 GAV 与子模块 `<parent>` 三行必须一致（默认 `relativePath ../pom.xml` 正确，勿画蛇添足） |
