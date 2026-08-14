package com.eval.darwin;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * 达尔文实跑验证主类。
 * 放在根包 com.eval.darwin（验证 01-startup-config.md：主类须在根包）。
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
public class DarwinTestApplication {
    public static void main(String[] args) {
        SpringApplication.run(DarwinTestApplication.class, args);
    }
}
