package com.eval.spring;

import org.springframework.util.concurrent.ListenableFuture;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Future;

/**
 * PMD 规则测试 fixture：ListenableFuture（Spring 6 / SpringBoot 3.x 已 @Deprecated）。
 * 规则3 AvoidDeprecatedListenableFuture → 应命中
 */
public class ListenableFutureCases {

    // ===== 规则3：ListenableFuture 废弃 API（应命中 3 处）=====

    public ListenableFuture<String> returnListenable() {        // ✗ 返回类型：应命中
        return null;
    }

    private ListenableFuture<Integer> listenableField;          // ✗ 字段类型：应命中

    public void consume(ListenableFuture<Boolean> param) {      // ✗ 参数类型：应命中
    }

    // ===== 合法用法（不应命中）=====

    public CompletableFuture<String> returnCompletableFuture() { // ✓ CompletableFuture：不应命中
        return CompletableFuture.completedFuture("ok");
    }

    public Future<String> returnFuture() {                      // ✓ java.util.concurrent.Future：不应命中
        return null;
    }
}
