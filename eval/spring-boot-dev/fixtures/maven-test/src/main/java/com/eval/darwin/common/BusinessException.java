package com.eval.darwin.common;

import lombok.Getter;

/**
 * 验证 05-exception-handling.md：业务异常继承 RuntimeException（非受检）。
 */
@Getter
public class BusinessException extends RuntimeException {
    private final int code;

    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
    }

    public BusinessException(String message) {
        this(400, message);
    }
}
