package demo;

import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import java.math.RoundingMode;
import static org.junit.jupiter.api.Assertions.*;

/** 项 1-12：BigDecimal 金额运算（回归 12 项） */
class A_BigDecimalTest {

    @Test
    void test01_stringCtorExact() {
        assertEquals("0.1", new BigDecimal("0.1").toString());
    }

    @Test
    void test02_doubleCtorInexact() {
        assertNotEquals("0.1", new BigDecimal(0.1).toString());
        assertEquals("0.1000000000000000055511151231257827021181583404541015625", new BigDecimal(0.1).toString());
    }

    @Test
    void test03_compareToIgnoresScale() {
        assertEquals(0, new BigDecimal("1.0").compareTo(new BigDecimal("1.00")));
    }

    @Test
    void test04_equalsComparesScale() {
        assertNotEquals(new BigDecimal("1.0"), new BigDecimal("1.00"));
    }

    @Test
    void test05_bareDivideThrows() {
        assertThrows(ArithmeticException.class,
                () -> new BigDecimal("1").divide(new BigDecimal("3")));
    }

    @Test
    void test06_divideWithScaleRounding() {
        assertEquals(new BigDecimal("0.33"),
                new BigDecimal("1").divide(new BigDecimal("3"), 2, RoundingMode.HALF_UP));
    }

    @Test
    void test07_setScaleHalfUp() {
        assertEquals(new BigDecimal("2.34"),
                new BigDecimal("2.335").setScale(2, RoundingMode.HALF_UP));
    }

    @Test
    void test08_stripTrailingZeros() {
        assertEquals(0, new BigDecimal("1.100").stripTrailingZeros()
                .compareTo(new BigDecimal("1.1")));
    }

    @Test
    void test09_immutable() {
        BigDecimal bd = new BigDecimal("1.00");
        bd.add(new BigDecimal("1"));
        assertEquals(new BigDecimal("1.00"), bd);
    }

    @Test
    void test10_absMinValueIntOverflow() {
        assertTrue(Math.abs(Integer.MIN_VALUE) < 0);
    }

    @Test
    void test11_byteMask0xFF() {
        assertEquals(255, (byte) -1 & 0xFF);
    }

    @Test
    void test12_valueOfExact() {
        assertEquals("0.1", BigDecimal.valueOf(0.1).toString());
    }
}
