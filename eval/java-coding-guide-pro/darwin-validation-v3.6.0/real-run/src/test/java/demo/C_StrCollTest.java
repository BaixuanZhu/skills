package demo;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.collection.ListUtil;
import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import org.junit.jupiter.api.Test;
import java.util.Arrays;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

/** 项 25-37：字符串/集合（回归 13 项） */
class C_StrCollTest {

    @Test
    void test25_isBlankCoversWhitespace() {
        assertTrue(StrUtil.isBlank(" "));
        assertTrue(StrUtil.isBlank(null));
        assertTrue(StrUtil.isNotBlank("a"));
    }

    @Test
    void test26_blankToDefaultVsEmptyToDefault() {
        assertEquals("x", StrUtil.blankToDefault("   ", "x"));
        assertEquals("   ", StrUtil.emptyToDefault("   ", "x"));
    }

    @Test
    void test27_subAfterLastSeparator() {
        assertEquals("gz", StrUtil.subAfter("a.tar.gz", ".", true));
        assertEquals("tar.gz", StrUtil.subAfter("a.tar.gz", ".", false));
    }

    @Test
    void test28_splitByLiteral() {
        List<String> ps = StrUtil.split("a.b.c", '.');
        assertEquals(Arrays.asList("a", "b", "c"), ps);
    }

    @Test
    void test29_caseConversion() {
        assertEquals("user_name", StrUtil.toUnderlineCase("userName"));
        assertEquals("userName", StrUtil.toCamelCase("user_name"));
    }

    @Test
    void test30_join() {
        assertEquals("1,2,3", StrUtil.join(",", Arrays.asList(1, 2, 3)));
    }

    @Test
    void test31_objectUtilEqualNullSafe() {
        assertTrue(ObjectUtil.equal(null, null));
        assertFalse(ObjectUtil.equal(null, "a"));
        assertTrue(ObjectUtil.equal("a", "a"));
    }

    @Test
    void test32_collUtilIsEmptyNullSafe() {
        java.util.Collection<Object> nil = null;
        assertTrue(CollUtil.isEmpty(nil));
        assertTrue(CollUtil.isEmpty(List.of()));
        assertFalse(CollUtil.isEmpty(List.of("x")));
    }

    @Test
    void test33_listUtilPartition() {
        List<List<Integer>> parts = ListUtil.partition(List.of(1, 2, 3, 4, 5), 2);
        assertEquals(3, parts.size());
        assertEquals(List.of(1, 2), parts.get(0));
        assertEquals(List.of(5), parts.get(2));
    }

    @Test
    void test34_arraysAsListFixedSize() {
        assertThrows(UnsupportedOperationException.class,
                () -> Arrays.asList(1, 2).add(3));
    }

    @Test
    void test35_beanUtilCopyOrderSourceFirst() {
        User src = new User(7L, "zhang");
        UserVO vo = new UserVO();
        BeanUtil.copyProperties(src, vo);
        assertEquals(7L, vo.getId());
        assertEquals("zhang", vo.getName());
    }

    @Test
    void test36_formatPlaceholder() {
        assertEquals("a-b", StrUtil.format("{}-{}", "a", "b"));
    }

    @Test
    void test37_trimToNull() {
        assertNull(StrUtil.trimToNull("   "));
        assertEquals("a", StrUtil.trimToNull(" a "));
    }
}
