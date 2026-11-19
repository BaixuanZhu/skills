package com.example.eval;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.util.NoSuchElementException;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

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

    /**
     * 金额口径：值用 compareTo（isEqualByComparingTo）比较，不用 equals（equals 连 scale 一起比）；
     * 两方法合同均为固定两位小数，故每次一并断 scale()==2，防「少写一次 setScale(2)」假绿。
     */
    private static void assertAmount(BigDecimal actual, String expected) {
        assertThat(actual).isEqualByComparingTo(expected);
        assertThat(actual.scale()).isEqualTo(2);
    }

    // ---------- quote：正向 ----------

    @Test
    void quote_returnsTotalWithoutDiscountBelowThreshold() {
        when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("10.00"));

        BigDecimal result = pricingService.quote("SKU-1", 3);

        assertAmount(result, "30.00");
        verify(priceRepository).findPrice("SKU-1");
    }

    @Test
    void quote_appliesDiscountAboveThreshold() {
        when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("25.00"));

        BigDecimal result = pricingService.quote("SKU-1", 5);

        // 25.00 * 5 = 125.00 >= 100.00 -> * 0.9 = 112.50
        assertAmount(result, "112.50");
    }

    @Test
    void quote_keepsScaleTwoForWholeNumberTotal() {
        when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("20.00"));

        BigDecimal result = pricingService.quote("SKU-1", 3);

        assertAmount(result, "60.00");
    }

    // ---------- quote：边界 ----------

    @Test
    void quote_acceptsQuantityOfOne() {
        // 桩值 10.999 与期望 11.00 不同，可证返回值经过了换算而非透传桩值
        when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("10.999"));

        BigDecimal result = pricingService.quote("SKU-1", 1);

        assertAmount(result, "11.00");
    }

    @Test
    void quote_doesNotApplyDiscountJustBelowThreshold() {
        when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("99.99"));

        BigDecimal result = pricingService.quote("SKU-1", 1);

        assertAmount(result, "99.99");
    }

    @Test
    void quote_appliesDiscountExactlyAtThreshold() {
        when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("50.00"));

        BigDecimal result = pricingService.quote("SKU-1", 2);

        // 50.00 * 2 = 100.00 恰好达阈值（>= 判定）-> * 0.9 = 90.00
        assertAmount(result, "90.00");
    }

    @Test
    void quote_roundsHalfUpToTwoDecimalsAfterDiscount() {
        when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("33.34"));

        BigDecimal result = pricingService.quote("SKU-1", 3);

        // 33.34 * 3 = 100.02 -> * 0.9 = 90.018 -> HALF_UP -> 90.02
        assertAmount(result, "90.02");
    }

    @Test
    void quote_roundsHalfUpToTwoDecimalsWithoutDiscount() {
        when(priceRepository.findPrice("SKU-1")).thenReturn(new BigDecimal("0.125"));

        BigDecimal result = pricingService.quote("SKU-1", 1);

        // 0.125 恰为半值：HALF_UP -> 0.13（HALF_EVEN 会得 0.12，可区分舍入口径）
        assertAmount(result, "0.13");
    }

    // ---------- quote：异常（非法输入被拒绝） ----------

    @ParameterizedTest
    @NullAndEmptySource
    @ValueSource(strings = { " ", "\t", "   " })
    void quote_throwsWhenSkuIsNullOrBlank(String sku) {
        assertThatThrownBy(() -> pricingService.quote(sku, 1))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("sku must not be blank");
        verifyNoInteractions(priceRepository);
    }

    @ParameterizedTest
    @ValueSource(ints = { 0, -1, -10 })
    void quote_throwsWhenQuantityIsNotPositive(int quantity) {
        assertThatThrownBy(() -> pricingService.quote("SKU-1", quantity))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("quantity must be positive");
        verifyNoInteractions(priceRepository);
    }

    @Test
    void quote_throwsWhenPriceNotFound() {
        when(priceRepository.findPrice("GONE")).thenReturn(null);

        assertThatThrownBy(() -> pricingService.quote("GONE", 1))
                .isInstanceOf(NoSuchElementException.class)
                .hasMessage("price not found: GONE");
        verify(priceRepository).findPrice("GONE");
    }

    // ---------- allocate：正向 ----------

    @Test
    void allocate_splitsEvenly() {
        BigDecimal result = pricingService.allocate(new BigDecimal("100.00"), 2);

        assertAmount(result, "50.00");
    }

    @Test
    void allocate_roundsDownWhenNextDigitBelowFive() {
        BigDecimal result = pricingService.allocate(new BigDecimal("100.00"), 3);

        // 100.00 / 3 = 33.333... -> 33.33
        assertAmount(result, "33.33");
    }

    // ---------- allocate：边界 ----------

    @Test
    void allocate_roundsHalfUpAtMidpoint() {
        BigDecimal result = pricingService.allocate(new BigDecimal("0.05"), 2);

        // 0.05 / 2 = 0.025 恰为半值：HALF_UP -> 0.03（HALF_EVEN 会得 0.02，可区分舍入口径）
        assertAmount(result, "0.03");
    }

    @Test
    void allocate_returnsScaleTwoForExactDivision() {
        BigDecimal result = pricingService.allocate(new BigDecimal("90.00"), 3);

        assertAmount(result, "30.00");
    }

    @Test
    void allocate_normalizesScaleForSinglePerson() {
        BigDecimal result = pricingService.allocate(new BigDecimal("5"), 1);

        // 输入 scale=0，合同固定两位小数 -> 5.00（仅比值的断言会漏掉该合同）
        assertAmount(result, "5.00");
    }

    @Test
    void allocate_returnsZeroWithScaleTwoForZeroAmount() {
        BigDecimal result = pricingService.allocate(BigDecimal.ZERO, 3);

        assertAmount(result, "0.00");
    }

    // ---------- allocate：异常（非法输入被拒绝） ----------

    @Test
    void allocate_throwsWhenAmountIsNull() {
        assertThatThrownBy(() -> pricingService.allocate(null, 2))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("amount must not be null");
    }

    @ParameterizedTest
    @ValueSource(ints = { 0, -1, -3 })
    void allocate_throwsWhenPeopleIsNotPositive(int people) {
        assertThatThrownBy(() -> pricingService.allocate(new BigDecimal("10.00"), people))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("people must be positive");
    }
}
