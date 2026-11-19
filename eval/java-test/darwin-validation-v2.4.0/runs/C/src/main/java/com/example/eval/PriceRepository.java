package com.example.eval;

import java.math.BigDecimal;

public interface PriceRepository {
    BigDecimal findPrice(String sku);
}
