package com.eval.demo;

import com.github.tomakehurst.wiremock.WireMockServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import static com.github.tomakehurst.wiremock.client.WireMock.okJson;
import static com.github.tomakehurst.wiremock.client.WireMock.post;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.options;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;

/**
 * 验证 06：WireMock 外部 HTTP stub。
 * stubFor + okJson + dynamicPort（随机端口，避免并行冲突）—— 模拟外部支付 API，可控可重复。
 */
class PaymentWireMockTest {

    static WireMockServer wireMock = new WireMockServer(options().dynamicPort());

    @BeforeAll
    static void start() {
        wireMock.start();
    }

    @AfterAll
    static void stop() {
        wireMock.stop();
    }

    @Test
    void should_stub_external_payment_api() {
        wireMock.stubFor(post(urlEqualTo("/api/charge"))
            .willReturn(okJson("{\"code\":0,\"data\":{\"paymentId\":\"PAY123\"}}")));

        given()
            .port(wireMock.port())
            .contentType("application/json")
            .body("{\"amount\":199}")
        .when()
            .post("/api/charge")
        .then()
            .statusCode(200)
            .body("data.paymentId", equalTo("PAY123"));
    }
}
