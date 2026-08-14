package com.eval.demo;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;

    @Transactional
    public Order createOrder(Long productId, Integer qty) {
        Order order = new Order();
        order.setProductId(productId);
        order.setQty(qty);
        order.setStatus("CREATED");
        return orderRepository.save(order);
    }
}
