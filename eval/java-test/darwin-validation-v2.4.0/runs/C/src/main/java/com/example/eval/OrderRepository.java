package com.example.eval;

import java.util.List;

public interface OrderRepository {
    boolean exists(String orderNo);
    void insert(String orderNo, List<String> skus);
}
