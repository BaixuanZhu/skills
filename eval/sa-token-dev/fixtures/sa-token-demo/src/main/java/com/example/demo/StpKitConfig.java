package com.example.demo;

import cn.dev33.satoken.config.SaTokenConfig;
import org.springframework.context.annotation.Configuration;

import jakarta.annotation.PostConstruct;

/**
 * 验证 skill 11-advanced §6「不同体系不同配置」的修正写法。
 * 正确方式（官方文档）：StpKit.USER 是 StpLogic 实例，直接 setConfig()。
 * 错误方式（skill 原文曾有）：StpKit.USER.setStpLogic(new StpLogic("user").setConfig(...)) —— StpLogic 无 setStpLogic 方法。
 */
@Configuration
public class StpKitConfig {

    @PostConstruct
    public void setSaTokenConfig() {
        SaTokenConfig adminConfig = new SaTokenConfig();
        adminConfig.setTokenName("satoken-admin");
        adminConfig.setTimeout(7200);
        StpKit.DEFAULT.setConfig(adminConfig);

        SaTokenConfig userConfig = new SaTokenConfig();
        userConfig.setTokenName("satoken-user");
        userConfig.setTimeout(2592000);
        // 修正写法：直接对 StpLogic 实例 setConfig（StpKit.USER 即 StpLogic）
        StpKit.USER.setConfig(userConfig);
    }
}
