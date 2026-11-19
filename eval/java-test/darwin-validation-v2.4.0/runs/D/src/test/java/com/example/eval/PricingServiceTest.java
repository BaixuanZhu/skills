package com.example.eval;

import java.math.BigDecimal;
import java.util.NoSuchElementException;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatExceptionOfType;
import static org.assertj.core.api.Assertions.assertThatNoException;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoMoreInteractions;
import static org.mockito.Mockito.when;

class PricingServiceTest {

    @Mock
    private PriceRepository priceRepository;

    private PricingService pricingService;
    private AutoCloseable mockHandle;

    @BeforeEach
    void setUp() {
        // pom 仅含 mockito-core，故用 MockitoAnnotations.openMocks 装配（不依赖 mockito-junit-jupiter）
        mockHandle = MockitoAnnotations.openMocks(this);
        pricingService = new PricingService(priceRepository);
    }

    @AfterEach
    void tearDown() throws Exception {
        mockHandle.close();
    }

    @Nested
    @DisplayName("quote(String sku, int quantity)")
    class QuoteTest {

        @Test
        @DisplayName("sku 为 null 时抛 IllegalArgumentException")
        void nullSku_throwsIllegalArgumentException() {
            assertThatExceptionOfType(IllegalArgumentException.class)
                    .isThrownBy(() -> pricingService.quote(null, 1))
                    .withMessage("sku must not be blank");
        }

        @Test
        @DisplayName("sku 为空字符串时抛 IllegalArgumentException")
        void emptySku_throwsIllegalArgumentException() {
            assertThatExceptionOfType(IllegalArgumentException.class)
                    .isThrownBy(() -> pricingService.quote("", 1))
                    .withMessage("sku must not be blank");
        }

        @Test
        @DisplayName("sku 为纯空白时抛 IllegalArgumentException")
        void blankSku_throwsIllegalArgumentException() {
            assertThatExceptionOfType(IllegalArgumentException.class)
                    .isThrownBy(() -> pricingService.quote("   ", 1))
                    .withMessage("sku must not be blank");
        }

        @Test
        @DisplayName("quantity 为 0 时抛 IllegalArgumentException")
        void zeroQuantity_throwsIllegalArgumentException() {
            assertThatExceptionOfType(IllegalArgumentException.class)
                    .isThrownBy(() -> pricingService.quote("SKU-1", 0))
                    .withMessage("quantity must be positive");
        }

        @Test
        @DisplayName("quantity 为负数时抛 IllegalArgumentException")
        void negativeQuantity_throwsIllegalArgumentException() {
            assertThatExceptionOfType(IllegalArgumentException.class)
                    .isThrownBy(() -> pricingService.quote("SKU-1", -3))
                    .withMessage("quantity must be positive");
        }

        @Test
        @DisplayName("价格不存在时抛 NoSuchElementException")
        void priceNotFound_throwsNoSuchElementException() {
            when(priceRepository.findPrice("SKU-404")).thenReturn(null);

            assertThatExceptionOfType(NoSuchElementException.class)
                    .isThrownBy(() -> pricingService.quote("SKU-404", 1))
                    .withMessage("price not found: SKU-404");

            verify(priceRepository).findPrice("SKU-404");
        }

        @Test
        @DisplayName("未达折扣门槛时按原价计算（单价 10 × 5 = 50.00）")
        void belowDiscountThreshold_noDiscount() {
            when(priceRepository.findPrice("SKU-A")).thenReturn(new BigDecimal("10.00"));

            BigDecimal total = pricingService.quote("SKU-A", 5);

            assertThat(total).isEqualByComparingTo("50.00");
            assertThat(total).hasScaleOf(2);
            verify(priceRepository).findPrice("SKU-A");
            verifyNoMoreInteractions(priceRepository);
        }

        @Test
        @DisplayName("总额恰好等于折扣门槛 100.00 时享受 9 折（边界值）")
        void exactlyAtDiscountThreshold_appliesDiscount() {
            when(priceRepository.findPrice("SKU-B")).thenReturn(new BigDecimal("20.00"));

            BigDecimal total = pricingService.quote("SKU-B", 5);

            assertThat(total).isEqualByComparingTo("90.00");
        }

        @Test
        @DisplayName("总额刚好低于门槛 99.99 时不打折（边界值）")
        void justBelowDiscountThreshold_noDiscount() {
            when(priceRepository.findPrice("SKU-C")).thenReturn(new BigDecimal("33.33"));

            BigDecimal total = pricingService.quote("SKU-C", 3);

            assertThat(total).isEqualByComparingTo("99.99");
        }

        @Test
        @DisplayName("超过门槛时打 9 折（单价 30 × 5 = 150 → 135.00）")
        void aboveDiscountThreshold_appliesDiscount() {
            when(priceRepository.findPrice("SKU-D")).thenReturn(new BigDecimal("30.00"));

            BigDecimal total = pricingService.quote("SKU-D", 5);

            assertThat(total).isEqualByComparingTo("135.00");
            assertThat(total).hasScaleOf(2);
        }

        @Test
        @DisplayName("打折结果按 HALF_UP 保留两位小数（166.65 × 0.9 = 149.985 → 149.99）")
        void discountRounding_halfUp() {
            when(priceRepository.findPrice("SKU-E")).thenReturn(new BigDecimal("33.33"));

            BigDecimal total = pricingService.quote("SKU-E", 5);

            assertThat(total).isEqualByComparingTo("149.99");
            assertThat(total).hasScaleOf(2);
        }

        @Test
        @DisplayName("不打折结果也按 HALF_UP 保留两位小数（0.005 × 1 → 0.01）")
        void noDiscountRounding_halfUp() {
            when(priceRepository.findPrice("SKU-F")).thenReturn(new BigDecimal("0.005"));

            BigDecimal total = pricingService.quote("SKU-F", 1);

            assertThat(total).isEqualByComparingTo("0.01");
            assertThat(total).hasScaleOf(2);
        }

        @Test
        @DisplayName("quantity 为 1 时结果等于单价（不打折情形）")
        void quantityOne_returnsUnitPrice() {
            when(priceRepository.findPrice("SKU-G")).thenReturn(new BigDecimal("12.34"));

            BigDecimal total = pricingService.quote("SKU-G", 1);

            assertThat(total).isEqualByComparingTo("12.34");
        }

        @Test
        @DisplayName("每次调用以入参 sku 查询价格仓库")
        void callsRepositoryWithGivenSku() {
            when(priceRepository.findPrice("SKU-H")).thenReturn(new BigDecimal("1.00"));

            pricingService.quote("SKU-H", 2);

            verify(priceRepository).findPrice("SKU-H");
            verifyNoMoreInteractions(priceRepository);
        }
    }

    @Nested
    @DisplayName("allocate(BigDecimal amount, int people)")
    class AllocateTest {

        @Test
        @DisplayName("amount 为 null 时抛 IllegalArgumentException")
        void nullAmount_throwsIllegalArgumentException() {
            assertThatExceptionOfType(IllegalArgumentException.class)
                    .isThrownBy(() -> pricingService.allocate(null, 2))
                    .withMessage("amount must not be null");
        }

        @Test
        @DisplayName("people 为 0 时抛 IllegalArgumentException")
        void zeroPeople_throwsIllegalArgumentException() {
            assertThatExceptionOfType(IllegalArgumentException.class)
                    .isThrownBy(() -> pricingService.allocate(new BigDecimal("10.00"), 0))
                    .withMessage("people must be positive");
        }

        @Test
        @DisplayName("people 为负数时抛 IllegalArgumentException")
        void negativePeople_throwsIllegalArgumentException() {
            assertThatExceptionOfType(IllegalArgumentException.class)
                    .isThrownBy(() -> pricingService.allocate(new BigDecimal("10.00"), -1))
                    .withMessage("people must be positive");
        }

        @Test
        @DisplayName("整除时平均分摊（100.00 / 4 = 25.00，保留两位小数）")
        void evenSplit() {
            BigDecimal share = pricingService.allocate(new BigDecimal("100.00"), 4);

            assertThat(share).isEqualByComparingTo("25.00");
            assertThat(share).hasScaleOf(2);
        }

        @Test
        @DisplayName("people 为 1 时金额原样保留两位小数")
        void singlePerson_returnsAmount() {
            BigDecimal share = pricingService.allocate(new BigDecimal("123.45"), 1);

            assertThat(share).isEqualByComparingTo("123.45");
            assertThat(share).hasScaleOf(2);
        }

        @Test
        @DisplayName("除不尽时按 HALF_UP 进位（0.05 / 2 = 0.025 → 0.03）")
        void rounding_halfUpRoundsUp() {
            BigDecimal share = pricingService.allocate(new BigDecimal("0.05"), 2);

            assertThat(share).isEqualByComparingTo("0.03");
            assertThat(share).hasScaleOf(2);
        }

        @Test
        @DisplayName("除不尽时按 HALF_UP 舍去（1.00 / 3 = 0.333… → 0.33）")
        void rounding_halfUpRoundsDown() {
            BigDecimal share = pricingService.allocate(new BigDecimal("1.00"), 3);

            assertThat(share).isEqualByComparingTo("0.33");
            assertThat(share).hasScaleOf(2);
        }

        @Test
        @DisplayName("金额为 0 时结果为 0.00")
        void zeroAmount_returnsZero() {
            BigDecimal share = pricingService.allocate(new BigDecimal("0.00"), 7);

            assertThat(share).isEqualByComparingTo("0.00");
            assertThat(share).hasScaleOf(2);
        }

        @Test
        @DisplayName("大量人数分摊仍保留两位小数")
        void manyPeople_keepsScale() {
            BigDecimal share = pricingService.allocate(new BigDecimal("1.00"), 300);

            assertThat(share).isEqualByComparingTo("0.00");
            assertThat(share).hasScaleOf(2);
        }

        @Test
        @DisplayName("不需要价格仓库参与，不产生交互")
        void noRepositoryInteraction() {
            assertThatNoException().isThrownBy(() -> pricingService.allocate(new BigDecimal("9.99"), 3));

            verifyNoMoreInteractions(priceRepository);
        }
    }
}
