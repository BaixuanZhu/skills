package com.eval.darwin.dto;

import lombok.Data;

/**
 * 验证 02-layered-arch.md：VO（出参），不含 password 等敏感字段。
 */
@Data
public class UserVO {
    private Long id;
    private String username;
    // 注意：不返回 password（脱敏）
}
