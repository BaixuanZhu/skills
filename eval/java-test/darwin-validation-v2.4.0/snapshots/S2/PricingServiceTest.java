package com.example.eval;

import java.math.BigDecimal;
import java.util.NoSuchElementException;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.verifyNoMoreInteractions;
import static org.mockito.Mockito.when;

/**
 * PricingService 纯单元测试：
 * - 外部依赖 PriceRepository 用 @Mock 注入（构造器注入，无被测类内部 new）。
 * - 金额断言统一 isEqualByComparingTo 比值 + 单独断 scale()，不用 equals。
 * - 异常断言断契约指定的具体异常类 + hasMessage，不落在 RuntimeException 根父类。
 */
class PricingServiceTest {

    @Mock
    private PriceRepository priceRepository;

    @InjectMocks
    private PricingService pricingService;

    private AutoCloseable mocks;

    @BeforeEach
    void setUp() {
        mocks = MockitoAnnotations.openMocks(this);
    }

    @AfterEach
    void tearDown() throws Exception {
        mocks.close();
    }

    // ==================== quote：正向 ====================

    @Test
    @DisplayName("quote 正向：未达折扣阈值，返回原价总额并固定两位小数")
    void quote_belowThresholdReturnsTotalWithoutDiscount() {
        when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("10.00"));

        BigDecimal result = pricingService.quote("SKU-1", 5);

        assertThat(result).isEqualByComparingTo("50.00");
        assertThat(result.scale()).isEqualTo(2);
        // mock 注入有效性：被测代码用的就是这个 mock 实例，且只查了一次价格
        verify(priceRepository).findPrice("SKU-1");
        verifyNoMoreInteractions(priceRepository);
    }

    @Test
    @DisplayName("quote 正向：超过阈值打九折")
    void quote_appliesDiscountAboveThreshold() {
        when(priceRepository.findPrice("SKU-4")).thenReturn(new BigDecimal("30.00"));

        BigDecimal result = pricingService.quote("SKU-4", 4);

        // 30 x 4 = 120 >= 100 -> 120 x 0.9 = 108.00
        assertThat(result).isEqualByComparingTo("108.00");
        assertThat(result.scale()).isEqualTo(2);
    }

    // ==================== quote：边界 ====================

    @Test
    @DisplayName("quote 边界：总额恰好等于阈值 100.00，折扣生效（>= 判定）")
    void quote_appliesDiscountAtExactThreshold() {
        when(priceRepository.findPrice("SKU-2")).thenReturn(new BigDecimal("100.00"));

        BigDecimal result = pricingService.quote("SKU-2", 1);

        // 100.00 x 0.9 = 90.00
        assertThat(result).isEqualByComparingTo("90.00");
        assertThat(result.scale()).isEqualTo(2);
    }

    @Test
    @DisplayName("quote 边界：总额略低于阈值 99.99，不打折")
    void quote_noDiscountJustBelowThreshold() {
        when(priceRepository.findPrice("SKU-3")).thenReturn(new BigDecimal("99.99"));

        BigDecimal result = pricingService.quote("SKU-3", 1);

        assertThat(result).isEqualByComparingTo("99.99");
    }

    @Test
    @DisplayName("quote 边界：折后 90.315 按 HALF_UP 进位为 90.32")
    void quote_roundsHalfUpToTwoDecimals() {
        when(priceRepository.findPrice("SKU-5")).thenReturn(new BigDecimal("11.15"));

        BigDecimal result = pricingService.quote("SKU-5", 9);

        // 11.15 x 9 = 100.35 -> x 0.9 = 90.315 -> setScale(2, HALF_UP) = 90.32
        assertThat(result).isEqualByComparingTo("90.32");
        assertThat(result.scale()).isEqualTo(2);
    }

    @Test
    @DisplayName("quote 边界：整数结果也强制两位小数（5 -> 5.00）")
    void quote_forcesScaleTwoOnWholeResult() {
        when(priceRepository.findPrice("SKU-6")).thenReturn(new BigDecimal("5"));

        BigDecimal result = pricingService.quote("SKU-6", 1);

        // 值比较对 5 与 5.00 都绿，scale() 断言才抓得住少写 setScale(2) 的回归
        assertThat(result).isEqualByComparingTo("5.00");
        assertThat(result.scale()).isEqualTo(2);
    }

    @Test
    @DisplayName("quote 边界：quantity=1 是最小合法值")
    void quote_acceptsMinimumQuantityOne() {
        when(priceRepository.findPrice("SKU-8")).thenReturn(new BigDecimal("20.00"));

        BigDecimal result = pricingService.quote("SKU-8", 1);

        assertThat(result).isEqualByComparingTo("20.00");
    }

    // ==================== quote：反向 / 异常 ====================

    @ParameterizedTest(name = "sku=[{0}]")
    @NullAndEmptySource
    @ValueSource(strings = {" ", "\t", "  \n "})
    @DisplayName("quote 反向：sku 为 null/空串/空白串抛 IllegalArgumentException")
    void quote_throwsOnNullOrBlankSku(String sku) {
        assertThatThrownBy(() -> pricingService.quote(sku, 1))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("sku must not be blank");
        verifyNoInteractions(priceRepository);
    }

    @ParameterizedTest(name = "quantity={0}")
    @ValueSource(ints = {0, -1, Integer.MIN_VALUE})
    @DisplayName("quote 反向：quantity 非正数抛 IllegalArgumentException")
    void quote_throwsOnNonPositiveQuantity(int quantity) {
        assertThatThrownBy(() -> pricingService.quote("SKU-7", quantity))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("quantity must be positive");
        verifyNoInteractions(priceRepository);
    }

    @Test
    @DisplayName("quote 异常：价格不存在抛 NoSuchElementException 并带 sku")
    void quote_throwsWhenPriceNotFound() {
        when(priceRepository.findPrice("UNKNOWN-1")).thenReturn(null);

        assertThatThrownBy(() -> pricingService.quote("UNKNOWN-1", 2))
                .isInstanceOf(NoSuchElementException.class)
                .hasMessage("price not found: UNKNOWN-1");
        verify(priceRepository).findPrice("UNKNOWN-1");
    }

    // ==================== allocate：正向 / 边界 ====================

    @Test
    @DisplayName("allocate 正向：整除得到两位小数金额")
    void allocate_dividesEvenly() {
        BigDecimal result = pricingService.allocate(new BigDecimal("100"), 4);

        assertThat(result).isEqualByComparingTo("25.00");
        assertThat(result.scale()).isEqualTo(2);
    }

    @Test
    @DisplayName("allocate 边界：除不尽向下取（1/3 -> 0.33）")
    void allocate_roundsDown() {
        BigDecimal result = pricingService.allocate(new BigDecimal("1"), 3);

        assertThat(result).isEqualByComparingTo("0.33");
        assertThat(result.scale()).isEqualTo(2);
    }

    @Test
    @DisplayName("allocate 边界：除不尽向上进位（2/3 -> 0.67）")
    void allocate_roundsUp() {
        BigDecimal result = pricingService.allocate(new BigDecimal("2"), 3);

        assertThat(result).isEqualByComparingTo("0.67");
        assertThat(result.scale()).isEqualTo(2);
    }

    @Test
    @DisplayName("allocate 边界：tie 时 HALF_UP 进位（0.005/1 -> 0.01）")
    void allocate_roundsHalfUpOnTie() {
        BigDecimal result = pricingService.allocate(new BigDecimal("0.005"), 1);

        assertThat(result).isEqualByComparingTo("0.01");
        assertThat(result.scale()).isEqualTo(2);
    }

    @Test
    @DisplayName("allocate 边界：people=1 时金额不变但 scale 固定为 2（42.5 -> 42.50）")
    void allocate_singlePersonKeepsAmount() {
        BigDecimal result = pricingService.allocate(new BigDecimal("42.5"), 1);

        assertThat(result).isEqualByComparingTo("42.50");
        assertThat(result.scale()).isEqualTo(2);
    }

    @Test
    @DisplayName("allocate 边界：amount=0 返回 0.00")
    void allocate_zeroAmount() {
        BigDecimal result = pricingService.allocate(BigDecimal.ZERO, 3);

        assertThat(result).isEqualByComparingTo("0.00");
        assertThat(result.scale()).isEqualTo(2);
    }

    @Test
    @DisplayName("allocate 边界（现状记录）：负数金额未被拒绝，按 HALF_UP 分摊")
    void allocate_dividesNegativeAmount() {
        BigDecimal result = pricingService.allocate(new BigDecimal("-100"), 3);

        assertThat(result).isEqualByComparingTo("-33.33");
    }

    // ==================== allocate：反向 / 异常 ====================

    @Test
    @DisplayName("allocate 反向：amount 为 null 抛 IllegalArgumentException")
    void allocate_throwsOnNullAmount() {
        assertThatThrownBy(() -> pricingService.allocate(null, 3))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("amount must not be null");
    }

    @ParameterizedTest(name = "people={0}")
    @ValueSource(ints = {0, -1, Integer.MIN_VALUE})
    @DisplayName("allocate 反向：people 非正数抛 IllegalArgumentException")
    void allocate_throwsOnNonPositivePeople(int people) {
        assertThatThrownBy(() -> pricingService.allocate(new BigDecimal("10"), people))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("people must be positive");
    }
}
