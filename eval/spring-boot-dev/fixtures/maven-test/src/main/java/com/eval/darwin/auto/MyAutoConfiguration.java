package com.eval.darwin.auto;

import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Bean;

/**
 * 验证 10-condition-bean.md：
 * - 3.x 用 @AutoConfiguration（非 @Configuration）
 * - @ConditionalOnClass + @ConditionalOnMissingBean 组合（starter 惯例）
 */
@AutoConfiguration
@ConditionalOnClass(MyService.class)
public class MyAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public MyService myService() {
        return new MyService();
    }
}
