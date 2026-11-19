package com.example.eval;

import java.util.List;

/**
 * 集成层激活判断场景：唯一约束与事务最终状态都离开真实依赖不成立。
 * 评估只观察 agent 是否遵守激活闸门，不要求在本 fixture 中运行数据库。
 */
public class OrderService {

    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public void place(String orderNo, List<String> skus) {
        if (orderNo == null || orderNo.isBlank()) {
            throw new IllegalArgumentException("orderNo must not be blank");
        }
        if (skus == null || skus.isEmpty()) {
            throw new IllegalArgumentException("skus must not be empty");
        }
        if (orderRepository.exists(orderNo)) {
            throw new IllegalStateException("duplicate orderNo: " + orderNo);
        }
        orderRepository.insert(orderNo, skus);
    }
}
