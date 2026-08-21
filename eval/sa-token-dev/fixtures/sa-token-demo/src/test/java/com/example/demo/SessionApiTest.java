package com.example.demo;

import cn.dev33.satoken.SaManager;
import cn.dev33.satoken.exception.SaTokenException;
import cn.dev33.satoken.listener.SaTokenEventCenter;
import cn.dev33.satoken.stp.StpUtil;
import cn.dev33.satoken.strategy.SaJsonStrategy;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 实跑验证 skill 关键示例（Sa-Token 1.46.0 + Redis + HTTP 请求驱动）：
 * 1. Session 类型安全集合读取 getList/getSet/getMap（v1.46.0+，lazy 语义）
 * 2. 侦听器注销前钩子 doBeforeLogout
 * 3. redis-template 默认序列化器类型（裁决盲评 B 疑点）
 * 4. SaJsonType 白名单方式（官方推荐 1）：Session 存取业务实体不报错
 * 5. SaJsonStrategy 初始化后不可注册（验证 skill 07 时序说明）
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class SessionApiTest {

    @Autowired
    private TestRestTemplate rest;

    @BeforeAll
    static void setup() {
        SaTokenEventCenter.registerListener(new MySaTokenListener());
    }

    private HttpHeaders authHeaders(Integer id) {
        String token = rest.getForObject("/doLogin?id=" + id, String.class);
        // StpKitConfig 验证了 setConfig 生效（默认体系 tokenName 已改为 satoken-admin），动态取 tokenName
        String tokenName = StpUtil.getTokenName();
        System.out.println("[diag] doLogin token=" + token + ", tokenName=" + tokenName);
        HttpHeaders headers = new HttpHeaders();
        headers.set(tokenName, token);
        return headers;
    }

    @Test
    void session_集合类型安全读取_getList_getSet_getMap() {
        HttpHeaders headers = authHeaders(10001);
        String body = rest.postForObject("/sessionOps", new HttpEntity<>(headers), String.class);
        assertTrue(body.contains("[a, b]"), "getList lazy 命中，实际: " + body);
        assertTrue(body.contains("admin"), "getSet 读取，实际: " + body);
        assertTrue(body.contains("math=90"), "getMap 读取，实际: " + body);
        assertTrue(body.contains("cached=[a, b]"), "lazy 二次读取应命中缓存，实际: " + body);
    }

    @Test
    void listener_注销前钩子触发() {
        HttpHeaders headers = authHeaders(10002);
        String body = rest.postForObject("/listenerLogout?id=10002", new HttpEntity<>(headers), String.class);
        assertTrue(body.contains("delta=1"), "doBeforeLogout 应触发一次，实际: " + body);
    }

    @Test
    void saJsonType_白名单_业务实体存取Session() {
        HttpHeaders headers = authHeaders(10003);
        String body = rest.postForObject("/sysUserOps", new HttpEntity<>(headers), String.class);
        assertEquals("name=zhang", body.trim(), "SaJsonType 方式应正常反序列化，实际: " + body);
    }

    @Test
    void redisTemplate_默认序列化器类型() {
        // 裁决盲评 B 疑点：sa-token-redis-template 默认序列化层类型
        String serializerName = SaManager.getSaSerializerTemplate().getClass().getName();
        System.out.println("默认序列化器: " + serializerName);
        // 官方文档：RedisTemplate 方案默认 String -> JSON 序列化（SaSerializerTemplateForJson）
        assertTrue(serializerName.contains("Json") || serializerName.contains("json"),
                "期望 JSON 序列化器，实际: " + serializerName);
    }

    @Test
    void saJsonStrategy_已初始化后不可注册() {
        // 验证 skill 07 时序说明：JSON 插件首次构建后 registerAllowType 抛异常（@PostConstruct 时机太晚）
        SaTokenException ex = assertThrows(SaTokenException.class,
                () -> SaJsonStrategy.instance.registerAllowType(SysUser.class));
        System.out.println("注册异常信息: " + ex.getMessage());
        assertTrue(ex.getMessage().contains("初始化") || ex.getMessage().contains("无法注册"));
    }
}
