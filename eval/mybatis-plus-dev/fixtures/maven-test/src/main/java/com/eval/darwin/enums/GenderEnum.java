package com.eval.darwin.enums;

import com.baomidou.mybatisplus.annotation.EnumValue;
import com.fasterxml.jackson.annotation.JsonValue;
import lombok.Getter;

/**
 * 枚举映射验证（强约束 #9）：
 * - @EnumValue 标注数据库存储的值字段（MP 据此映射）
 * - @JsonValue 标注 JSON 序列化输出值（否则 Jackson 默认输出枚举名 MALE/FEMALE）
 */
@Getter
public enum GenderEnum {
    MALE(1, "男"),
    FEMALE(2, "女");

    @EnumValue
    private final int code;
    @JsonValue
    private final String label;

    GenderEnum(int code, String label) {
        this.code = code;
        this.label = label;
    }
}
