package com.eval.demo;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * 验证 03：@WebMvcTest 切片测试。
 * 只加载 Web 层（Controller），Service 用 @MockBean mock —— 不起全量 Context，秒级启动。
 */
@WebMvcTest(OrderController.class)
class OrderControllerSliceTest {

    @Autowired MockMvc mockMvc;

    @MockBean OrderService orderService;

    @Test
    void should_return_created_order() throws Exception {
        Order order = new Order();
        order.setId(1L);
        order.setProductId(1L);
        order.setQty(2);
        order.setStatus("CREATED");
        when(orderService.createOrder(anyLong(), any())).thenReturn(order);

        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"productId\":1,\"qty\":2}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1))
            .andExpect(jsonPath("$.status").value("CREATED"));
    }
}
