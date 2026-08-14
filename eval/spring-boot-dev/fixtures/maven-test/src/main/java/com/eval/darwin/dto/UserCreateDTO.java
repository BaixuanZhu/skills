package com.eval.darwin.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import lombok.Data;
import org.hibernate.validator.constraints.Length;

import java.util.List;

/**
 * 验证 04-validation.md：Bean 参数校验 + 组合注解 + properties 插值。
 */
@Data
public class UserCreateDTO {

    @NotBlank(message = "{user.username.notblank}")
    @Length(min = 3, max = 20, message = "{user.username.length}")
    private String username;

    @ValidPhone                                   // 组合注解（不散落正则）
    private String phone;

    @Email(message = "{user.email.invalid}")
    private String email;

    @NotBlank
    @Length(min = 8, max = 32)
    private String password;

    @Valid
    private List<@Valid String> tags;
}
