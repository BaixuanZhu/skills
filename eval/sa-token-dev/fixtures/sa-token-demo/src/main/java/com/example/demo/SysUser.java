package com.example.demo;

import cn.dev33.satoken.json.SaJsonType;

/**
 * 验证 skill 07 §序列化安全的官方推荐方式 1：
 * 业务实体实现 SaJsonType 标记接口即可加入 JSON 全局类型白名单，无需额外配置。
 * （官方推荐方式 2：main 方法里 SpringApplication.run 之前 registerAllowType；
 *  方式 3：resources/META-INF/satoken/sa-json-type.list SPI 文件）
 */
public class SysUser implements SaJsonType {
    public String name;
}
