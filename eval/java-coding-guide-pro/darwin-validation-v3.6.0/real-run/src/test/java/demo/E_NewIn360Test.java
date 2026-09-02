package demo;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.bean.copier.CopyOptions;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Constructor;
import java.lang.reflect.Modifier;
import java.math.BigDecimal;
import java.util.Locale;

import static org.junit.jupiter.api.Assertions.*;

/**
 * v3.6.0 新增处方实跑验证：
 * ① 11 §9 状态/类型码 → 枚举；② 11 §10 常量类放置（final + private 构造）；
 * ③ 10 速查表千分位行 String.format(Locale.US, "%,.2f", bd)；
 * ④ 06 速查表「拷贝到已有对象（忽略 null）」行 BeanUtil.copyProperties + CopyOptions。
 */
class E_NewIn360Test {

    @Test
    void test44_enumExtractedFromDuplicatedLiteral() {
        // "PENDING" 字面量 ≥2 处 → 提取枚举，枚举常量可直接 == 比较
        OrderStatus a = OrderStatus.PENDING;
        OrderStatus b = OrderStatus.valueOf("PENDING");
        assertTrue(a == b, "同枚举常量同一实例，== 比较成立");
        assertNotSame(OrderStatus.PENDING, OrderStatus.PAID);
        assertEquals(3, OrderStatus.values().length, "有限取值封闭集合");
    }

    @Test
    void test45_constantsClassPlacementPattern() throws Exception {
        // 跨包共享阈值/配置 → 按域拆分常量类：final + private 构造禁实例化
        assertEquals(3, OrderConstants.MAX_RETRY);
        assertEquals(5000L, OrderConstants.TIMEOUT_MS);
        assertTrue(Modifier.isFinal(OrderConstants.class.getModifiers()), "常量类应为 final");
        Constructor<?>[] ctors = OrderConstants.class.getDeclaredConstructors();
        assertEquals(1, ctors.length, "只有显式 private 构造");
        assertTrue(Modifier.isPrivate(ctors[0].getModifiers()), "构造必须 private 禁实例化");
    }

    @Test
    void test46_thousandSeparatorExplicitLocale() {
        BigDecimal amount = new BigDecimal("1234.567")
            .setScale(2, java.math.RoundingMode.HALF_UP);
        // 显式 Locale.US：逗号分组 + 点小数
        assertEquals("1,234.57", String.format(Locale.US, "%,.2f", amount));
        // 反证：默认 locale 依赖环境——德国 locale 得到点分组 + 逗号小数，解析必错
        assertEquals("1.234,57", String.format(Locale.GERMANY, "%,.2f", amount),
            "隐式 locale 的千分位形态——显式传 Locale 的理由");
    }

    @Test
    void test47_copyToExistingIgnoreNull() {
        User src = new User(7L, null);          // name 为 null
        UserVO target = new UserVO();
        target.setId(1L);
        target.setName("kept");
        BeanUtil.copyProperties(src, target, CopyOptions.create().ignoreNullValue());
        assertEquals(7L, target.getId(), "非 null 字段正常覆盖");
        assertEquals("kept", target.getName(), "null 字段不覆盖已有值");
    }

    @Test
    void test48_copyDefaultOverwritesWithNull() {
        // 默认 CopyOptions（不 ignoreNullValue）：null 直接覆盖——忽略 null 必须显式开启
        User src = new User(7L, null);
        UserVO target = new UserVO();
        target.setName("kept");
        BeanUtil.copyProperties(src, target);
        assertNull(target.getName(), "默认行为 null 覆盖，ignoreNullValue 非默认");
    }
}
