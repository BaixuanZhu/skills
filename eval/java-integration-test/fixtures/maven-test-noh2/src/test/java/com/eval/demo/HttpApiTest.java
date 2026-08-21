package com.eval.demo;

import io.restassured.RestAssured;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static io.restassured.RestAssured.given;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.notNullValue;

/**
 * 验证 06 头号坑：@SpringBootTest(RANDOM_PORT) + @Transactional 回滚【失效】。
 *
 * RANDOM_PORT 下 HTTP 请求走真实 Servlet 容器线程，与测试线程不在同一事务。
 * 测试线程的 @Transactional 只回滚测试线程的事务，HTTP 线程的提交不受影响 → 数据残留。
 *
 * 实跑验证手段：两个方法固定顺序，方法 2 断言方法 1 的 HTTP 写入仍然存在（count=1）。
 * 若 @Transactional 回滚生效，方法 2 应看到 count=0。
 *
 * 注意：@TestMethodOrder + @Order 是【故意】违反技能 A 级规则「测试不依赖顺序」——
 * 这里它是评估 fixture 内部用来验证「回滚失效」机制的观察手段，不是技能推荐做法。
 *
 * 无 H2 项目：@ServiceConnection 连真实 PostgreSQL 容器（推荐镜像 17.11-alpine）。
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Transactional
@Testcontainers
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class HttpApiTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17.11-alpine");

    @LocalServerPort int port;
    @Autowired OrderRepository orderRepository;

    @BeforeEach
    void setup() {
        RestAssured.port = port;
    }

    @Test
    @Order(1)
    void create_order_via_http() {
        given()
            .contentType("application/json")
            .body("{\"productId\":1,\"qty\":2}")
        .when()
            .post("/api/orders")
        .then()
            .statusCode(200)
            .body("id", notNullValue())
            .body("status", equalTo("CREATED"));
        // 方法结束：测试线程 @Transactional 回滚，但 HTTP 已提交 → 数据残留
    }

    @Test
    @Order(2)
    void second_test_sees_residual_data() {
        // 若回滚生效 → count=0；若失效（HTTP 独立线程已提交）→ count=1
        assertThat(orderRepository.count()).isEqualTo(1L);
    }
}
