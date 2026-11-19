package com.example.eval;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.NoSuchElementException;

/**
 * 评估固定被测类：金额口径、具体异常、mock 注入、四维覆盖均有可验证陷阱。
 * 仅用于 java-test 达尔文评估，不是业务实现。
 */
public class PricingService {

    private static final BigDecimal DISCOUNT_THRESHOLD = new BigDecimal("100.00");
    private static final BigDecimal DISCOUNT_RATE = new BigDecimal("0.9");

    private final PriceRepository priceRepository;

    public PricingService(PriceRepository priceRepository) {
        this.priceRepository = priceRepository;
    }

    public BigDecimal quote(String sku, int quantity) {
        if (sku == null || sku.isBlank()) {
            throw new IllegalArgumentException("sku must not be blank");
        }
        if (quantity <= 0) {
            throw new IllegalArgumentException("quantity must be positive");
        }
        BigDecimal unitPrice = priceRepository.findPrice(sku);
        if (unitPrice == null) {
            throw new NoSuchElementException("price not found: " + sku);
        }

        BigDecimal total = unitPrice.multiply(BigDecimal.valueOf(quantity));
        if (total.compareTo(DISCOUNT_THRESHOLD) >= 0) {
            total = total.multiply(DISCOUNT_RATE);
        }
        return total.setScale(2, RoundingMode.HALF_UP);
    }

    public BigDecimal allocate(BigDecimal amount, int people) {
        if (amount == null) {
            throw new IllegalArgumentException("amount must not be null");
        }
        if (people <= 0) {
            throw new IllegalArgumentException("people must be positive");
        }
        return amount.divide(BigDecimal.valueOf(people), 2, RoundingMode.HALF_UP);
    }
}
