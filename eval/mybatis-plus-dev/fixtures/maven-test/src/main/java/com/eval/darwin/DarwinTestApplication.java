package com.eval.darwin;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.eval.darwin.mapper")
public class DarwinTestApplication {
    public static void main(String[] args) {
        SpringApplication.run(DarwinTestApplication.class, args);
    }
}
