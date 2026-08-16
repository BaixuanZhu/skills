# 01 · 模板使用（assets/maven-multimodule 机械用法）

本文是 `assets/maven-multimodule/` 的唯一使用说明：结构、插件清单、占位符、init.mjs 生成、多模块扩展、自检。生成与自检均为零依赖 node 脚本，跨平台。

## 模板结构

```
assets/maven-multimodule/
├── pom.xml                        # 聚合根：packaging=pom + <modules> + 插件/依赖版本收敛
├── gitignore.txt                  # 生成时改名为 .gitignore（target/、IDE 文件、.flattened-pom.xml）——模板内非点名存放（发布平台只收白名单扩展名与常规文件名）
├── sample-core/
│   └── pom.xml                    # 基础库模块（普通 jar，无 repackage）
└── sample-app/                    # 可执行模块（spring-boot-maven-plugin repackage）
    ├── pom.xml                    # 依赖 sample-core + web + test
    └── src/
        ├── main/java/com/example/Application.java   # 主类（挪到 groupId 路径）
        └── main/resources/application.yml
```

根 pom 已收敛：`dependencyManagement`（spring-boot-dependencies BOM `{{BOOT_VERSION}}` + `cn.hutool:hutool-bom` import（hutool 模块按需引）+ `hutool-all` 全量条目 + `{{GROUP_ID}}:sample-core` 模块间依赖）+ `pluginManagement`（enforcer / flatten / jacoco / spotless / compiler / surefire / failsafe / resources / spring-boot / source / javadoc / deploy，版本全在 `<properties>`）+ 公共依赖 lombok（optional，继承全部子模块）+ 内置阿里云 `repositories` / `pluginRepositories`（国内下载加速）。**子模块因此一律不带版本号。**

## 插件清单（激活 / 按需两档）

| 档 | 插件 | 作用 |
|---|---|---|
| 激活（根 pom 声明，随构建自动跑） | maven-enforcer-plugin | 环境门禁：Maven ≥ 3.6.3、JDK ≥ `${java.version}`，不达标即构建失败 |
| 激活 | flatten-maven-plugin | CI-friendly 版本：install/deploy 用解析了 `${revision}` 的 `.flattened-pom.xml`（已 gitignore） |
| 激活 | jacoco-maven-plugin | 覆盖率：prepare-agent + report（`target/site/jacoco/`） |
| 激活 | spotless-maven-plugin | 格式化：`mvn spotless:apply`（google-java-format AOSP） |
| 按需（已管版本+配置，子模块裸声明即用） | maven-failsafe-plugin | 集成测试（`*IT` 类，verify 阶段）——加集成测试的模块声明它 |
| 按需 | maven-source-plugin | 发布库模块时附源码 jar |
| 按需 | maven-javadoc-plugin | 发布库模块时附 javadoc jar |
| 按需 | maven-deploy-plugin | app 模块已设 `maven.deploy.skip=true`（fat jar 不进仓库），deploy 只留给库模块 |

质量门禁插件（PMD / SpotBugs）不内置——归 `java-coding-quality` 技能；容器化用 `mvn spring-boot:build-image`（spring-boot 插件内建）。

## 占位符（5 个，只出现在 pom.xml 与 application.yml 文本中，全部由 init.mjs 替换，勿手改）

| 占位符 | 含义 | 示例值 |
|---|---|---|
| `{{GROUP_ID}}` | groupId，同时决定 Java 包路径 | `com.acme.order` |
| `{{ARTIFACT_ID}}` | 根 artifactId（项目名）+ `spring.application.name` | `order-service` |
| `{{VERSION}}` | 项目版本——写入根 `<revision>` 属性，全工程 GAV / `<parent>` 坐标引用 `${revision}` | `1.0.0-SNAPSHOT` |
| `{{JAVA_VERSION}}` | JDK 版本（compiler `release` + enforcer 下限） | `21` |
| `{{BOOT_VERSION}}` | Spring Boot 版本（BOM import） | `3.5.16` |

## 初始化（scripts/init.mjs 一条命令）

```bash
# 多模块（库模块 + 可执行模块，名字来自 C1 问询）
node <技能目录>/scripts/init.mjs /path/to/order-service \
    --group com.acme.order --artifact order-service \
    --boot 3.5.16 --jdk 21 --core order-core --app order-app

# 单模块（--single 裁掉库模块及其全部引用）
node <技能目录>/scripts/init.mjs /path/to/ping-api \
    --group cn.demo.ping --artifact ping-api --single
```

| 参数 | 必填 | 默认 | 说明 |
|---|---|---|---|
| `--group` | ✓ | — | groupId，同时决定 Java 包路径（须为合法 Java 包名，非法直接拒绝） |
| `--artifact` | ✓ | — | 根 artifactId（项目名）+ `spring.application.name` |
| `--boot` / `--jdk` | | `3.5.16` / `21` | C2 问询结果（兼容表见 SKILL.md） |
| `--version` | | `1.0.0-SNAPSHOT` | 写入根 `<revision>` 属性 |
| `--core` / `--app` | | `<artifact>-core` / `<artifact>-app` | 模块名（C1 问询结果） |
| `--single` | | — | 单模块形态：删库模块目录及其三处引用（`<modules>` 行 / dependencyManagement 条目 / app 依赖） |

脚本内部依次：①复制模板 → ②单模块裁剪（`--single` 删库模块的三处 pom 引用）→ ③模块重命名（sample-core/app 的 pom 引用与目录一次对齐；函数替换不回扫，名字互含子串也不腐蚀——**必须在占位符展开之前**，用户值写入后不再经过任何替换）→ ④替换 5 个占位符（最后一步文本改写）→ ⑤主类暂存到 java 根、清掉整个模板包壳 `com/`、再挪到 groupId 包路径改 package 行（目标包嵌在 `com/example` 之下也不误删）→ ⑥残留终检（`{{...}}` / `com.example` / 主类存在 / 顶层目录恰为模块集；仅当 groupId 自身包含 com.example 时先剥离再匹配，不遮蔽真残留）。groupId（含 Java 保留字包段、过长）/ artifact / 模块名（尾点、同名、仅大小写不同、撞 sample-core/sample-app 保留名、pom.xml、target 构建输出目录、与根 artifactId 同名）/ 版本号非法、`--single` 与 `--core` 同给、未知参数或多余位置参数、目标已存在文件而非目录、**目标目录非空（隐藏条目如 .git 不影响）**时直接拒绝。

生成后跑 `node <技能目录>/scripts/self-check.mjs <目标目录> --validate` 收尾（详见 SKILL.md「自检与交付」）。

## 多模块扩展（初始化时增加第 3+ 个模块）

`init.mjs` 产出 core + app 两个模块；更多模块在生成后手动补（**只服务本次初始化**——工程建成后再加模块，直接参照工程内现有模块结构即可，不回本技能）：

- **增库模块**：`cp -r order-core <新名>` → 改其 pom 的 `<artifactId>`/`<name>` → 根 `<modules>` 加行 → 需要被其他模块依赖时，根 `dependencyManagement` 加 `<groupId>:<新名>` 条目。
- **增可执行模块**：`cp -r order-app <新名>` → 同上三步（自带 repackage 与主类，把包目录与主类挪到不冲突的路径）。
- **删模块**：`rm -rf <目录>` + 根 `<modules>` 去行 + 其他模块对它的 `<dependency>` 删除。

## ✗ 禁止 → ✓ 推荐

唯一生成路径、聚合规则、版本收敛、占位符零残留、repackage 归属等核心规则见 SKILL.md「核心强约束」，此处只列强约束未覆盖的模板细节：

| ✗ 禁止 | ✓ 推荐 |
|---|---|
| 需要资源过滤时直接开 filtering 用 `${...}` | 先配 `@..@` 分隔符（`${}` 与 Spring 占位符冲突）；模板默认不开过滤 |
| 用 maven-release-plugin 管发版 | release plugin 不兼容 CI-friendly 版本——用 `${revision}` + flatten：`mvn deploy -Drevision=1.0.0` |
| 公司内网 / 海外环境担心内置阿里云镜像拖慢构建 | 用户级 settings.xml 的 mirror 优先级更高、自动接管；确无需要也可整段删 `<repositories>` / `<pluginRepositories>` |
| 手动增删模块后漏改根 `<modules>` / 改根 GAV 后 `<parent>` 不同步 | 同步根 `<modules>`（自检第三查会拦孤儿 / 缺失）；根 GAV 与子模块 `<parent>` 三行一致（默认 `relativePath ../pom.xml` 正确，勿画蛇添足） |
