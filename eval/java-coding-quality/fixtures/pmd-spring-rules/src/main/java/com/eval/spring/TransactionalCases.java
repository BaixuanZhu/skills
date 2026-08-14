package com.eval.spring;

import org.springframework.transaction.annotation.Transactional;

/**
 * PMD 规则测试 fixture：@Transactional 相关陷阱。
 * 规则1 TransactionalOnNonProxyableMethod：private/static/final 方法 → 应命中
 * 规则2 TransactionalMissingRollbackFor：缺 rollbackFor → 应命中
 */
public class TransactionalCases {

    // ===== 规则1：@Transactional 标 private/static/final（应命中 3 处）=====

    @Transactional                              // ✗ private：应命中（代理失效）
    private void privateTxMethod() { }

    @Transactional                              // ✗ static：应命中（代理失效）
    public static void staticTxMethod() { }

    @Transactional                              // ✗ final：应命中（代理失效）
    public final void finalTxMethod() { }

    @Transactional                              // ✓ public 非 final：不应命中
    public void normalTxMethod() { }

    @Transactional                              // ✓ protected 非 final：不应命中
    protected void protectedTxMethod() { }

    // ===== 规则2：@Transactional 缺 rollbackFor（应命中 2 处）=====

    @Transactional                              // ✗ 缺 rollbackFor：应命中（受检异常不回滚）
    public void noRollbackFor() throws Exception { }

    @Transactional(rollbackFor = Exception.class)  // ✓ 有 rollbackFor：不应命中
    public void withRollbackFor() throws Exception { }

    @Transactional(noRollbackFor = Error.class)    // ✗ 只有 noRollbackFor 无 rollbackFor：应命中
    public void onlyNoRollbackFor() { }

    @Transactional("someTx")                    // ✗ 只有 value 无 rollbackFor：应命中
    public void onlyValue() { }
}
