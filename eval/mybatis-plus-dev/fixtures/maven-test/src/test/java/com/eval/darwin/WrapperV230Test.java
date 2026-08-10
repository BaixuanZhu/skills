package com.eval.darwin;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.eval.darwin.entity.DeptStatVO;
import com.eval.darwin.entity.UserDO;
import com.eval.darwin.enums.GenderEnum;
import com.eval.darwin.mapper.UserMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * v2.3.0 改动达尔文实跑验证。
 * 每个测试方法对应一条本次改动涉及的强约束/反模式，验证技能里的代码片段能编译且语义正确。
 * 类级 @Transactional：每个测试方法结束自动回滚，避免测试间数据污染。
 */
@SpringBootTest
@Transactional
class WrapperV230Test {

    @Autowired
    private UserMapper userMapper;

    // ========== 强约束 #11：字段引用必须用方法引用（Lambda） ==========

    /**
     * 验证 LambdaQueryWrapper + 方法引用编译通过且查询正确（强约束 #11）。
     * 对应 05-wrapper.md §1.1 范式 + 08-antipattern.md #24 正例。
     */
    @Test
    void lambdaQueryWrapper_方法引用_查询正确() {
        // 技能推荐范式：new LambdaQueryWrapper<>().eq(UserDO::getName, ...)
        List<UserDO> users = userMapper.selectList(
                new LambdaQueryWrapper<UserDO>().eq(UserDO::getName, "Tom"));

        assertEquals(1, users.size());
        assertEquals("Tom", users.get(0).getName());
    }

    /**
     * 验证方法引用链式条件（05-wrapper.md §3 常用条件）。
     */
    @Test
    void lambdaQueryWrapper_链式条件() {
        List<UserDO> users = userMapper.selectList(
                new LambdaQueryWrapper<UserDO>()
                        .eq(UserDO::getStatus, 1)
                        .ge(UserDO::getAge, 25)
                        .orderByDesc(UserDO::getAge));

        assertFalse(users.isEmpty());
        // 全部满足 status=1 且 age>=25
        assertTrue(users.stream().allMatch(u -> u.getStatus() == 1 && u.getAge() >= 25));
    }

    /**
     * 验证 select 投影用方法引用（05-wrapper.md §4）。
     */
    @Test
    void lambdaQueryWrapper_select投影() {
        List<UserDO> users = userMapper.selectList(
                new LambdaQueryWrapper<UserDO>()
                        .select(UserDO::getId, UserDO::getName)
                        .eq(UserDO::getAge, 25));

        assertEquals(1, users.size());
        assertNotNull(users.get(0).getId());
        assertNotNull(users.get(0).getName());
    }

    // ========== 05-wrapper.md §2：LambdaUpdateWrapper（更新侧方法引用） ==========

    /**
     * 验证 LambdaUpdateWrapper.set 方法引用置 null（强约束 #4 方法引用版 + 05-wrapper.md §2）。
     * 对应 08-antipattern.md #2 正例、03-entity.md §4。
     */
    @Test
    void lambdaUpdateWrapper_set置null() {
        // 先插入一条供更新的数据
        UserDO seed = new UserDO().setName("NullTest").setAge(40).setStatus(1).setGender(GenderEnum.MALE).setDeptId(300L);
        userMapper.insert(seed);
        Long id = seed.getId();

        // 技能推荐范式：LambdaUpdateWrapper + 方法引用置 null
        userMapper.update(null, new LambdaUpdateWrapper<UserDO>()
                .eq(UserDO::getId, id)
                .set(UserDO::getAge, null));

        UserDO updated = userMapper.selectById(id);
        assertNull(updated.getAge(), "LambdaUpdateWrapper.set(UserDO::getAge, null) 应将 age 置为 null");
    }

    /**
     * 验证 LambdaUpdateWrapper.setSql 拼接原生片段（05-wrapper.md §2）。
     * version = version + 1 这类引用列自身的表达式无方法引用对应，用 setSql。
     */
    @Test
    void lambdaUpdateWrapper_setSql原生片段() {
        UserDO seed = new UserDO().setName("VersionTest").setAge(20).setStatus(1).setGender(GenderEnum.FEMALE).setDeptId(400L).setVersion(0);
        userMapper.insert(seed);
        Long id = seed.getId();

        userMapper.update(null, new LambdaUpdateWrapper<UserDO>()
                .eq(UserDO::getId, id)
                .set(UserDO::getStatus, 0)
                .setSql("version = version + 1"));

        UserDO updated = userMapper.selectById(id);
        assertEquals(0, updated.getStatus());
        assertEquals(1, updated.getVersion(), "setSql 应正确执行 version = version + 1");
    }

    // ========== 强约束 #3：Wrapper 能力边界 → XML ==========

    /**
     * 验证聚合 + GROUP BY + HAVING 走 XML（强约束 #3 + 08-antipattern.md #25）。
     * Wrapper 表达不了，必须 XML。
     */
    @Test
    void 聚合查询走XML() {
        // 部门 200 有 3 个用户（Alice/Bob/Eve），部门 100 有 2 个（Tom/Jerry）
        DeptStatVO stat = userMapper.selectDeptStat(2);

        assertNotNull(stat);
        // userCount > 2 的只有部门 200（3 人）
        assertEquals(200L, stat.getDeptId());
        assertEquals(3L, stat.getUserCount());
    }

    /**
     * 验证窗口函数 ROW_NUMBER() OVER 走 XML（强约束 #3 + 08-antipattern.md #25）。
     * 对应反模式：✗ w.apply("ROW_NUMBER() OVER (...) = 1")
     */
    @Test
    void 窗口函数走XML() {
        List<DeptStatVO> topUsers = userMapper.selectTopUserPerDept();

        // 每个部门 age 最大的用户（部门 100: Jerry=30, 部门 200: Bob=35）
        assertNotNull(topUsers);
        // H2 MySQL 模式下窗口函数应正常工作
        assertFalse(topUsers.isEmpty());
    }

    /**
     * 验证联表分页走 XML（强约束 #3 + 06-page.md §4）。
     * IPage 入参非 null，MP 自动改写 LIMIT + COUNT。
     */
    @Test
    void 联表分页走XML() {
        Page<DeptStatVO> page = new Page<>(1, 10);
        IPage<DeptStatVO> result = userMapper.selectDeptStatPage(page, 1);

        assertNotNull(result);
        assertTrue(result.getTotal() >= 2, "部门 100(2人) 和 200(3人) 都满足 count>1");
        assertFalse(result.getRecords().isEmpty());
    }

    // ========== 强约束 #6：分页插件（验证 selectPage 正常工作） ==========

    /**
     * 验证分页插件配置正确（强约束 #6 + 02-config.md §1）。
     * selectPage 不返回全量、total 正确——证明 PaginationInnerInterceptor + jsqlparser 生效。
     * 注：类级 @Transactional 回滚，每个方法看到的都是初始 5 条。
     */
    @Test
    void 分页插件生效() {
        Page<UserDO> page = new Page<>(1, 2);
        IPage<UserDO> result = userMapper.selectPage(page,
                new LambdaQueryWrapper<UserDO>().eq(UserDO::getDeleted, 0));

        assertEquals(2, result.getRecords().size(), "每页 2 条");
        assertEquals(5L, result.getTotal(), "total 应为初始 5 条");
        assertEquals(3, result.getPages(), "5 条数据每页 2 条，总页数 3");
    }

    // ========== 05-wrapper.md §7：空值语义 ==========

    /**
     * 验证 eq 传 null 不忽略条件，生成 col = NULL 匹配 0 行（05-wrapper.md §7，实跑纠正）。
     * 经 MP 3.5.17 实跑 + 官方文档核实：eq(col, null) 默认 condition=true，
     * 生成 WHERE col = NULL，NULL = NULL 为 unknown，匹配 0 行（非忽略、非查空）。
     */
    @Test
    void eq传null生成等于NULL匹配0行() {
        // name=null 时 eq 生成 WHERE name = NULL，匹配 0 行
        List<UserDO> empty = userMapper.selectList(
                new LambdaQueryWrapper<UserDO>().eq(UserDO::getName, null));

        assertEquals(0, empty.size(),
                "eq(col, null) 生成 col = NULL，匹配 0 行（不是忽略，不是返回全部）");
    }

    /**
     * 验证三参重载 eq(condition, field, val) 条件性跳过（05-wrapper.md §7 正解）。
     * condition=false 时该条件不加入 SQL，等价于无过滤，返回全部。
     */
    @Test
    void eq三参重载condition为false时跳过() {
        String name = null;
        // condition = (name != null) = false → 该条件不拼入 SQL，返回全部
        List<UserDO> all = userMapper.selectList(
                new LambdaQueryWrapper<UserDO>().eq(name != null, UserDO::getName, name));

        assertEquals(5, all.size(),
                "三参重载 condition=false 时该条件被跳过，返回全部 5 条");
    }

    /**
     * 验证 eqOrIsNull（3.5.17+）值为 null 时自动转 IS NULL（05-wrapper.md §7）。
     */
    @Test
    void eqOrIsNull值为null时转ISNULL() {
        // 插入一条数据后，用 LambdaUpdateWrapper.set 强制把 deleted 置 null
        // （insert 默认 NOT_NULL 策略不会写入 null，需 update.set 绕过，正是强约束 #4 的场景）
        UserDO seed = new UserDO().setName("NullDeleted").setAge(20).setStatus(1)
                .setGender(GenderEnum.MALE).setDeptId(600L);
        userMapper.insert(seed);
        userMapper.update(null, new LambdaUpdateWrapper<UserDO>()
                .eq(UserDO::getId, seed.getId())
                .set(UserDO::getDeleted, null));

        // eqOrIsNull(deleted, null) 应生成 IS NULL，查到该记录
        List<UserDO> nullDeleted = userMapper.selectList(
                new LambdaQueryWrapper<UserDO>().eqOrIsNull(UserDO::getDeleted, null));

        assertTrue(nullDeleted.stream().anyMatch(u -> "NullDeleted".equals(u.getName())),
                "eqOrIsNull(col, null) 应转为 IS NULL 查到该记录");
    }

    /**
     * 验证查空值用 isNull 而非 eq(field, null)（05-wrapper.md §7 + 08-antipattern.md #9）。
     */
    @Test
    void 查空值用isNull() {
        // 先置一条 age=null
        UserDO seed = new UserDO().setName("NullAge").setStatus(1).setGender(GenderEnum.MALE).setDeptId(500L);
        userMapper.insert(seed);

        // isNull 正确查出 age 为 null 的记录
        List<UserDO> nullAgeUsers = userMapper.selectList(
                new LambdaQueryWrapper<UserDO>().isNull(UserDO::getAge));

        assertTrue(nullAgeUsers.stream().anyMatch(u -> "NullAge".equals(u.getName())),
                "isNull 应查出 age 为 null 的记录");
    }

    // ========== 强约束 #9：枚举映射 ==========

    /**
     * 验证枚举 @EnumValue 映射正确（强约束 #9 + 03-entity.md §7）。
     * 数据库存 1/2，查出来应是 GenderEnum.MALE/FEMALE。
     */
    @Test
    void 枚举映射正确() {
        UserDO tom = userMapper.selectOne(
                new LambdaQueryWrapper<UserDO>().eq(UserDO::getName, "Tom"));

        assertNotNull(tom);
        assertEquals(GenderEnum.MALE, tom.getGender(), "@EnumValue 应将数据库的 1 映射为 MALE");

        UserDO alice = userMapper.selectOne(
                new LambdaQueryWrapper<UserDO>().eq(UserDO::getName, "Alice"));

        assertNotNull(alice);
        assertEquals(GenderEnum.FEMALE, alice.getGender(), "@EnumValue 应将数据库的 2 映射为 FEMALE");
    }

    /**
     * 验证枚举字段作为查询条件（Lambda 方法引用 + 枚举）。
     */
    @Test
    void 枚举字段作为查询条件() {
        List<UserDO> males = userMapper.selectList(
                new LambdaQueryWrapper<UserDO>().eq(UserDO::getGender, GenderEnum.MALE));

        assertTrue(males.size() >= 3, "Tom/Jerry/Bob 都是 MALE");
        assertTrue(males.stream().allMatch(u -> u.getGender() == GenderEnum.MALE));
    }

    // ========== 05-wrapper.md §8：Wrapper 不可复用 ==========

    /**
     * 验证 Wrapper 不可复用（05-wrapper.md §8 + 08-antipattern.md #8）。
     * 复用同一实例第二次查询条件叠加。
     */
    @Test
    void wrapper不可复用_每次new新的() {
        // 正确范式：每次 new 一个新的
        List<UserDO> r1 = userMapper.selectList(new LambdaQueryWrapper<UserDO>().eq(UserDO::getAge, 25));
        List<UserDO> r2 = userMapper.selectList(new LambdaQueryWrapper<UserDO>().eq(UserDO::getAge, 25));

        assertEquals(r1.size(), r2.size(), "每次 new 新 Wrapper，两次查询结果应一致");
    }

    // ========== 05-wrapper.md §1.2 编译期验证 ==========

    /**
     * 编译期验证：方法引用 UserDO::getXxx 能编译通过，证明 getter 存在。
     * 若 UserDO 改名（如 getName→getUsername），此处编译失败——正是方法引用的价值。
     * 此测试无需运行期断言，编译通过即验证。
     */
    @Test
    void 方法引用编译期检查() {
        // 若把这行改成 UserDO::getNonExistField，编译期即报错（vs 字符串 "non_exist" 运行时才报错）
        LambdaQueryWrapper<UserDO> w = Wrappers.<UserDO>lambdaQuery()
                .eq(UserDO::getName, "Tom")
                .ne(UserDO::getStatus, 0)
                .gt(UserDO::getAge, 18);

        List<UserDO> users = userMapper.selectList(w);
        assertFalse(users.isEmpty());
    }
}
