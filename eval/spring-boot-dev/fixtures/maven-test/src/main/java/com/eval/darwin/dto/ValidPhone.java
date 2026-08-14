package com.eval.darwin.dto;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;
import jakarta.validation.ReportAsSingleViolation;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

import java.lang.annotation.*;

/**
 * 验证 04-validation.md「组合注解」：手机号校验封装一次，到处复用。
 * @Constraint(validatedBy = {}) 表示纯组合，无需自定义校验器。
 * @ReportAsSingleViolation 只报组合注解的 message，不透出子注解违反。
 */
@NotBlank
@Pattern(regexp = "^1[3-9]\\d{9}$", message = "{phone.invalid}")
@Size(min = 11, max = 11)
@ReportAsSingleViolation
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Constraint(validatedBy = {})
public @interface ValidPhone {
    String message() default "{phone.invalid}";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
