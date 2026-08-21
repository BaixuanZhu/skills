package com.eval.demo;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * 验证 02/06：@SpringBootTest(MOCK 默认) + @Transactional 回滚有效。
 * MOCK 模式下 HTTP 请求在测试线程内分发，@Transactional 包裹整个测试方法。
 * 无 H2 项目：@ServiceConnection 连真实 PostgreSQL 容器（推荐镜像 17.11-alpine）。
 */
@SpringBootTest
@Transactional
@Testcontainers
class ServiceLayerTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17.11-alpine");

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
