package demo;

import cn.hutool.core.text.CharSequenceUtil;
import cn.hutool.core.util.StrUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import org.junit.jupiter.api.Test;
import org.mapstruct.factory.Mappers;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.net.InetSocketAddress;
import java.net.SocketTimeoutException;
import java.util.concurrent.TimeUnit;
import static org.junit.jupiter.api.Assertions.*;

/** 项 38-42：v3.5.0 新增/变更声明（OkHttp 超时、SLF4J+Logback、Jackson、MapStruct、StrUtil 门面事实） */
class D_NewIn350Test {

    @Test
    void test38_okhttpReadTimeoutEnforced() throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/", ex -> {
            try { Thread.sleep(2000); } catch (InterruptedException ignored) {}
            byte[] b = "ok".getBytes();
            ex.sendResponseHeaders(200, b.length);
            ex.getResponseBody().write(b);
            ex.close();
        });
        server.start();
        OkHttpClient client = new OkHttpClient.Builder()
                .connectTimeout(2, TimeUnit.SECONDS)
                .readTimeout(300, TimeUnit.MILLISECONDS)
                .build();
        Request req = new Request.Builder()
                .url("http://127.0.0.1:" + server.getAddress().getPort() + "/")
                .build();
        assertThrows(SocketTimeoutException.class, () -> client.newCall(req).execute());
        server.stop(0);
    }

    @Test
    void test39_slf4j2Logback15Placeholder() {
        Logger log = LoggerFactory.getLogger("darwin");
        log.info("x={}", 42);
        assertTrue(LoggerFactory.getILoggerFactory().getClass().getName().toLowerCase().contains("logback"),
                "SLF4J 2.0.13 应绑定 Logback 1.5.x，实际工厂: "
                        + LoggerFactory.getILoggerFactory().getClass().getName());
    }

    @Test
    void test40_jacksonRoundTrip() throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(new User(1L, "a"));
        User back = mapper.readValue(json, User.class);
        assertEquals(1L, back.getId());
        assertEquals("a", back.getName());
    }

    @Test
    void test41_mapstructProcessorGenerated() {
        UserMapper mapper = Mappers.getMapper(UserMapper.class);
        UserVO vo = mapper.toVO(new User(9L, "mapped"));
        assertEquals(9L, vo.getId());
        assertEquals("mapped", vo.getName());
    }

    @Test
    void test42_strUtilFacadeApiFact() {
        assertEquals(StrUtil.isBlank(" "), CharSequenceUtil.isBlank(" "));
        assertEquals(StrUtil.isBlank(""), CharSequenceUtil.isBlank(""));
        assertEquals("user_name", CharSequenceUtil.toUnderlineCase("userName"));
    }
}
