package com.eval.darwin.config;

import com.eval.darwin.event.UserRegisteredEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

/**
 * 验证 08-events.md：
 * - @EventListener 默认同步无事务感知
 * - @TransactionalEventListener(AFTER_COMMIT) 事务提交后才触发
 * - fallbackExecution = true：无事务环境也触发
 */
@Slf4j
@Component
public class EventConfig {

    // ✗ 问题：默认同步，publishEvent 时立即触发，不管事务
    @EventListener
    public void onEventSync(UserRegisteredEvent event) {
        log.info("同步监听（无事务感知）: {}", event.username());
    }

    // ✓ 正确：事务提交后才触发（注册回滚则不发邮件）
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT, fallbackExecution = true)
    public void onEventAfterCommit(UserRegisteredEvent event) {
        log.info("事务提交后监听: {}", event.username());
    }
}
