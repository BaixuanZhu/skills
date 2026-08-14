package com.eval.spring;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.concurrent.ListenableFuture;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Future;

/**
 * 对抗性测试 + 候选规则验证。
 */
public class AdversarialCases {

    // ===== 规则1 对抗：@Transactional 不在方法上（构造器/字段），不应命中 =====

    @Transactional                              // 构造器上的 @Transactional（无意义但不该报规则1）
    public AdversarialCases() { }

    @Transactional                              // 字段上的 @Transactional（异常用法，但不该报规则1）
    private Object someField;

    // ===== 规则1 对抗：全限定写法，应命中 =====

    @org.springframework.transaction.annotation.Transactional  // 全限定名，private → 应命中规则1
    private void fullyQualifiedPrivate() { }

    // ===== 规则2 对抗：rollbackForClassName / 多参数含 rollbackFor，不应命中 =====

    @Transactional(rollbackForClassName = "java.lang.Exception")
    public void withRollbackForClassName() { }

    @Transactional(value = "tx1", rollbackFor = RuntimeException.class, readOnly = true)
    public void multiParamWithRollbackFor() { }

    // ===== 规则3 对抗：import 但未使用 ListenableFuture =====

    public CompletableFuture<String> ok() { return null; }

    // ===== 候选 A：@Value 注入静态字段（应命中 1）=====

    @Value("${app.timeout}")                    // ✗ @Value + static：永远 0/null
    private static long timeout;

    @Value("${app.name}")                       // ✓ @Value + 非 static：正常
    private String name;

    // ===== 候选 B：@Async 返回非 void/Future（应命中 2）=====

    @Async
    public String sendString() { return "x"; }  // ✗ 返回 String：调用方拿 null

    @Async
    public int compute() { return 42; }         // ✗ 返回 int

    @Async
    public void sendVoid() { }                  // ✓ void

    @Async
    public CompletableFuture<String> sendFuture() { return null; }

    @Async
    public Future<Integer> sendRawFuture() { return null; }
}

