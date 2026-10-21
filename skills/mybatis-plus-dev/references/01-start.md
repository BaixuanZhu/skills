# 依赖与快速开始

> 适用于 MyBatis-Plus 3.5.x。核心：选对 starter → 加 `@MapperScan` → 直接用 `BaseMapper`。

## 1. 添加依赖

> **依赖通用规则**：所有坐标 `com.baomidou:mybatis-plus-*`，同一项目内版本统一；切勿同时引入 `mybatis` / `mybatis-spring-boot-starter` / `mybatis-spring`（会与 MP 自带 MyBatis 冲突）。

**SpringBoot 3.x（Maven）**
```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
    <version>3.5.17</version>
</dependency>
```
- SpringBoot 2.x：换用 `mybatis-plus-boot-starter`；SpringBoot 4.x（需 MP ≥ 3.5.13）：换用 `mybatis-plus-spring-boot4-starter`（映射见 SKILL.md「版本与依赖」表）。

**分页必引（v3.5.9+）**：
```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-jsqlparser</artifactId>
    <version>3.5.17</version>
</dependency>
```
> JDK8 项目改用 `mybatis-plus-jsqlparser-4.9`（同版本号）。不引 jsqlparser，`PaginationInnerInterceptor` 无法工作（静默失效，无报错）。

> 3.4 时代的 `PaginationInterceptor` 已废弃，3.5.x 一律用 `MybatisPlusInterceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.XXX))`。老项目升级时若仍见 `PaginationInterceptor`，是没改完。

## 2. 最小配置


数据源照常配 `spring.datasource.*`（url / username / password / driver-class-name）。MP 自动接手，无需额外 `SqlSessionFactoryBean`。


> 进阶配置（分页插件、逻辑删除、自动填充、乐观锁）见 `02-config.md`；实体字段映射、主键策略、null 处理见 `03-entity.md`。
