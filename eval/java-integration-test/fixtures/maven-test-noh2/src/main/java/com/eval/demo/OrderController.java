package com.eval.demo;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;

    @PostMapping
    public Order create(@RequestBody CreateOrderRequest request) {
        return orderService.createOrder(request.productId(), request.qty());
    }

    public record CreateOrderRequest(Long productId, Integer qty) {
    }
}
