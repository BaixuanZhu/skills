package com.eval.demo;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * 验证 04：Testcontainers 真实 PostgreSQL 替代 H2。
 * @DataJpaTest 默认用 H2 替换数据源；这里 @AutoConfigureTestDatabase(replace = NONE) 禁用替换，
 * 让 @ServiceConnection（Spring Boot 3.1+）连接真实 PostgreSQL 容器 —— 消除 H2 方言差异。
 */
@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class OrderRepositoryTestcontainersTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired OrderRepository orderRepository;

    @Test
    void should_save_and_load_on_real_postgres() {
        Order order = new Order();
        order.setProductId(1L);
        order.setQty(2);
        order.setStatus("CREATED");
        Order saved = orderRepository.save(order);

        assertThat(saved.getId()).isNotNull();
        assertThat(orderRepository.findById(saved.getId())).isPresent();
    }
}
