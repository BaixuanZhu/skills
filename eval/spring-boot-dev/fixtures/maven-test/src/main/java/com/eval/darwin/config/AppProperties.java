package com.eval.darwin.config;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

/**
 * 验证 03-config-properties.md：@ConfigurationProperties + @Validated + 松散绑定。
 * application.yml 里写 app.user-name，Java 字段 userName 能绑定（松散绑定）。
 */
@Data
@ConfigurationProperties(prefix = "app")
@Validated
public class AppProperties {

    @NotBlank
    private String name;

    @Min(1)
    private int maxSize;

    // 注意：yml 用 user-name，字段用 userName（松散绑定生效）
    // @Value("${app.userName}") 则读不到（@Value 不松散绑定）
    private String userName;
}
