package com.eval.darwin.event;

/**
 * 验证 08-events.md：事件用 record（POJO，4.2+ 无需继承 ApplicationEvent）。
 */
public record UserRegisteredEvent(Long userId, String username) {
}
