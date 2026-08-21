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
 * 验证 04（v1.3.0 定位修复）：无 H2 项目 → 需要真实依赖的集成测试默认 Testcontainers。
 * 项目 pom 没有 H2（对照 maven-test fixture），@DataJpaTest + @AutoConfigureTestDatabase(replace = NONE)
 * + @ServiceConnection 连真实 PostgreSQL 容器 —— 镜像用推荐值 postgres:17.11-alpine。
 */
@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class OrderRepositoryTestcontainersTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17.11-alpine");

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
