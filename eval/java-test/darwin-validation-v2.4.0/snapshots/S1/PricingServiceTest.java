package com.example.eval;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.verifyNoMoreInteractions;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullSource;
import org.junit.jupiter.params.provider.ValueSource;

/**
 * PricingService 单元测试。
 *
 * 覆盖四个陷阱维度：
 * 1. 金额口径：所有返回值必须是 scale=2 的 BigDecimal（用 equals 语义校验 scale）。
 * 2. 具体异常：精确的异常类型 + 精确的异常消息，不接受宽松的 RuntimeException。
 * 3. mock 注入：手动 mock PriceRepository（pom 只有 mockito-core，无 mockito-junit-jupiter），
 *    校验入参、调用次数，以及校验失败路径上不得触达 repository。
 * 4. 四维覆盖：等价类 + 边界值 + 舍入模式（HALF_UP 与 HALF_EVEN 可区分点）+ 校验顺序。
 */
class PricingServiceTest {

    private PriceRepository priceRepository;
    private PricingService service;

    @BeforeEach
    void setUp() {
        priceRepository = mock(PriceRepository.class);
        service = new PricingService(priceRepository);
    }

    // ------------------------------------------------------------------
    // quote(String sku, int quantity)
    // ------------------------------------------------------------------

    @Nested
    @DisplayName("quote: 入参校验")
    class QuoteValidation {

        @ParameterizedTest(name = "sku = {0} 抛 IllegalArgumentException")
        @NullSource
        @ValueSource(strings = {"", "   ", "\t\n"})
        void blankSkuThrowsIllegalArgumentException(String sku) {
            assertThatThrownBy(() -> service.quote(sku, 1))
                    .isExactlyInstanceOf(IllegalArgumentException.class)
                    .hasMessage("sku must not be blank");

            // 校验失败不得触达 repository
            verifyNoInteractions(priceRepository);
        }

        @ParameterizedTest(name = "quantity = {0} 抛 IllegalArgumentException")
        @ValueSource(ints = {0, -1, Integer.MIN_VALUE})
        void nonPositiveQuantityThrowsIllegalArgumentException(int quantity) {
            assertThatThrownBy(() -> service.quote("SKU-1", quantity))
                    .isExactlyInstanceOf(IllegalArgumentException.class)
                    .hasMessage("quantity must be positive");

            verifyNoInteractions(priceRepository);
        }

        @Test
        @DisplayName("sku 与 quantity 同时非法时先报 sku 错（校验顺序）")
        void blankSkuTakesPrecedenceOverBadQuantity() {
            assertThatThrownBy(() -> service.quote("", 0))
                    .isExactlyInstanceOf(IllegalArgumentException.class)
                    .hasMessage("sku must not be blank");

            verifyNoInteractions(priceRepository);
        }

        @Test
        @DisplayName("价格缺失抛 NoSuchElementException（而非 IllegalArgumentException）")
        void missingPriceThrowsNoSuchElementException() {
            when(priceRepository.findPrice("SKU-404")).thenReturn(null);

            assertThatThrownBy(() -> service.quote("SKU-404", 1))
                    .isExactlyInstanceOf(java.util.NoSuchElementException.class)
                    .hasMessage("price not found: SKU-404");

            verify(priceRepository, times(1)).findPrice("SKU-404");
            verifyNoMoreInteractions(priceRepository);
        }
    }

    @Nested
    @DisplayName("quote: 金额与折扣口径")
    class QuotePricing {

        @Test
        @DisplayName("低于阈值不打折，且结果 scale=2")
        void belowThresholdNoDiscount() {
            when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("19.99"));

            BigDecimal result = service.quote("SKU-1", 1);

            assertThat(result).isEqualTo(new BigDecimal("19.99")); // equals 校验 scale
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("总额恰好等于 100.00 时仍打折（compareTo >= 0 边界包含）")
        void exactlyAtThresholdGetsDiscount() {
            when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("50.00"));

            BigDecimal result = service.quote("SKU-1", 2);

            assertThat(result).isEqualTo(new BigDecimal("90.00"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("阈值判断是 compareTo 而非 equals：整数 scale 的 100 同样打折")
        void thresholdUsesCompareToNotEquals() {
            // unitPrice scale=0 → total = 100（scale 0），equals("100.00") 为 false 但 compareTo 为 0
            when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("100"));

            BigDecimal result = service.quote("SKU-1", 1);

            assertThat(result).isEqualTo(new BigDecimal("90.00"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("总额 99.98 不打折（阈值下边界外）")
        void justBelowThresholdNoDiscount() {
            when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("49.99"));

            BigDecimal result = service.quote("SKU-1", 2);

            assertThat(result).isEqualTo(new BigDecimal("99.98"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("总额 100.02 打折后 90.018 → HALF_UP 进位为 90.02")
        void discountResultRoundsHalfUp() {
            when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("50.01"));

            BigDecimal result = service.quote("SKU-1", 2);

            assertThat(result).isEqualTo(new BigDecimal("90.02"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("典型促销价 19.99 x 6 = 119.94 → x0.9 = 107.946 → 107.95")
        void realisticDiscountRounding() {
            when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("19.99"));

            BigDecimal result = service.quote("SKU-1", 6);

            assertThat(result).isEqualTo(new BigDecimal("107.95"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("舍入模式是 HALF_UP 而非 HALF_EVEN：0.005 应进位为 0.01")
        void roundingIsHalfUpNotHalfEven() {
            when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("0.005"));

            BigDecimal result = service.quote("SKU-1", 1);

            // HALF_EVEN 会得到 0.00，HALF_UP 得到 0.01
            assertThat(result).isEqualTo(new BigDecimal("0.01"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("不足半分舍去：0.004 → 0.00")
        void belowHalfRoundsDown() {
            when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("0.004"));

            BigDecimal result = service.quote("SKU-1", 1);

            assertThat(result).isEqualByComparingTo("0.00");
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("结果始终补齐到 scale=2（整数价格 30 x 1 → 30.00）")
        void resultAlwaysScaleTwo() {
            when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("30"));

            BigDecimal result = service.quote("SKU-1", 1);

            assertThat(result).hasToString("30.00");
            assertThat(result).hasScaleOf(2);
        }
    }

    @Nested
    @DisplayName("quote: mock 交互")
    class QuoteRepositoryInteraction {

        @Test
        @DisplayName("成功路径调用 findPrice 恰好一次，且传入原始 sku")
        void callsFindPriceExactlyOnceWithSku() {
            when(priceRepository.findPrice("SKU-9")).thenReturn(new BigDecimal("10.00"));

            service.quote("SKU-9", 3);

            verify(priceRepository, times(1)).findPrice("SKU-9");
            verifyNoMoreInteractions(priceRepository);
        }

        @Test
        @DisplayName("不同 sku 各自命中各自的 stub（mock 按参数分发）")
        void stubPerSku() {
            when(priceRepository.findPrice("SKU-A")).thenReturn(new BigDecimal("10.00"));
            when(priceRepository.findPrice("SKU-B")).thenReturn(new BigDecimal("20.00"));

            assertThat(service.quote("SKU-A", 1)).isEqualByComparingTo("10.00");
            assertThat(service.quote("SKU-B", 1)).isEqualByComparingTo("20.00");

            verify(priceRepository).findPrice("SKU-A");
            verify(priceRepository).findPrice("SKU-B");
            verifyNoMoreInteractions(priceRepository);
        }
    }

    // ------------------------------------------------------------------
    // allocate(BigDecimal amount, int people)
    // ------------------------------------------------------------------

    @Nested
    @DisplayName("allocate: 入参校验")
    class AllocateValidation {

        @Test
        @DisplayName("amount 为 null 抛 IllegalArgumentException")
        void nullAmountThrowsIllegalArgumentException() {
            assertThatThrownBy(() -> service.allocate(null, 2))
                    .isExactlyInstanceOf(IllegalArgumentException.class)
                    .hasMessage("amount must not be null");
        }

        @ParameterizedTest(name = "people = {0} 抛 IllegalArgumentException")
        @ValueSource(ints = {0, -1, Integer.MIN_VALUE})
        void nonPositivePeopleThrowsIllegalArgumentException(int people) {
            assertThatThrownBy(() -> service.allocate(new BigDecimal("10.00"), people))
                    .isExactlyInstanceOf(IllegalArgumentException.class)
                    .hasMessage("people must be positive");
        }

        @Test
        @DisplayName("amount 与 people 同时非法时先报 amount 错（校验顺序）")
        void nullAmountTakesPrecedenceOverBadPeople() {
            assertThatThrownBy(() -> service.allocate(null, 0))
                    .isExactlyInstanceOf(IllegalArgumentException.class)
                    .hasMessage("amount must not be null");
        }
    }

    @Nested
    @DisplayName("allocate: 金额口径与舍入")
    class AllocateRounding {

        @Test
        @DisplayName("整除结果补齐 scale=2：100 / 4 → 25.00")
        void exactDivisionPadsScale() {
            BigDecimal result = service.allocate(new BigDecimal("100"), 4);

            assertThat(result).hasToString("25.00");
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("除不尽截断到分：10.00 / 3 → 3.33")
        void nonExactDivisionTruncatesToCents() {
            BigDecimal result = service.allocate(new BigDecimal("10.00"), 3);

            assertThat(result).isEqualTo(new BigDecimal("3.33"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("半分进位 HALF_UP：0.05 / 2 = 0.025 → 0.03（非 HALF_EVEN 的 0.02）")
        void halfCentRoundsUp() {
            BigDecimal result = service.allocate(new BigDecimal("0.05"), 2);

            assertThat(result).isEqualTo(new BigDecimal("0.03"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("负数金额同样 HALF_UP（远离零方向）：-0.05 / 2 = -0.025 → -0.03")
        void negativeHalfCentRoundsAwayFromZero() {
            BigDecimal result = service.allocate(new BigDecimal("-0.05"), 2);

            assertThat(result).isEqualTo(new BigDecimal("-0.03"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("负数除不尽：-10.00 / 3 → -3.33")
        void negativeAmountTruncates() {
            BigDecimal result = service.allocate(new BigDecimal("-10.00"), 3);

            assertThat(result).isEqualTo(new BigDecimal("-3.33"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("零金额：0.00 / 5 → 0.00")
        void zeroAmount() {
            BigDecimal result = service.allocate(new BigDecimal("0.00"), 5);

            assertThat(result).isEqualByComparingTo("0.00");
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("单人全额：1.00 / 1 → 1.00")
        void singlePersonGetsFullAmount() {
            BigDecimal result = service.allocate(new BigDecimal("1.00"), 1);

            assertThat(result).isEqualTo(new BigDecimal("1.00"));
            assertThat(result).hasScaleOf(2);
        }

        @Test
        @DisplayName("allocate 是纯计算，不触达 PriceRepository")
        void allocateDoesNotTouchRepository() {
            service.allocate(new BigDecimal("10.00"), 3);

            verifyNoInteractions(priceRepository);
        }
    }
}
