package com.eval.demo;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * 验证 02/06：@SpringBootTest(MOCK 默认) + @Transactional 回滚有效。
 * MOCK 模式下 HTTP 请求在测试线程内分发，@Transactional 包裹整个测试方法。
 */
@SpringBootTest
@Transactional
class ServiceLayerTest {

    @Autowired OrderService orderService;
    @Autowired OrderRepository orderRepository;

    @Test
    void should_create_order_in_transaction() {
        Order order = orderService.createOrder(1L, 2);
        assertThat(order.getId()).isNotNull();
        // 测试方法内可见写入的数据（同事务）
        assertThat(orderRepository.count()).isEqualTo(1);
        // 方法结束 → @Transactional 回滚 → 数据库干净（供其他测试方法验证）
    }
}
