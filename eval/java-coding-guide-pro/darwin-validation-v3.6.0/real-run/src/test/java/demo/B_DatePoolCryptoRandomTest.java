package demo;

import cn.hutool.core.date.DateUtil;
import cn.hutool.crypto.SecureUtil;
import cn.hutool.crypto.digest.BCrypt;
import org.junit.jupiter.api.Test;
import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;

/** 项 13-24：日期 3 + 线程池 1 + 加密 6 + 随机 2（回归 12 项） */
class B_DatePoolCryptoRandomTest {

    @Test
    void test13_dateUtilThreadSafe() throws Exception {
        String expect = DateUtil.format(DateUtil.parse("2026-08-23 10:00:00"), "yyyy-MM-dd HH:mm:ss");
        ExecutorService pool = Executors.newFixedThreadPool(10);
        CountDownLatch latch = new CountDownLatch(20);
        AtomicInteger wrong = new AtomicInteger();
        for (int i = 0; i < 20; i++) {
            pool.submit(() -> {
                String got = DateUtil.format(DateUtil.parse("2026-08-23 10:00:00"), "yyyy-MM-dd HH:mm:ss");
                if (!expect.equals(got)) wrong.incrementAndGet();
                latch.countDown();
            });
        }
        latch.await();
        pool.shutdown();
        assertEquals(0, wrong.get());
    }

    @Test
    void test14_explicitZoneId() {
        LocalDateTime sh = LocalDateTime.now(ZoneId.of("Asia/Shanghai"));
        LocalDateTime utc = LocalDateTime.now(ZoneId.of("UTC"));
        long diff = sh.atZone(ZoneId.of("Asia/Shanghai")).toInstant().toEpochMilli()
                - utc.atZone(ZoneId.of("UTC")).toInstant().toEpochMilli();
        assertTrue(Math.abs(diff) < 5000, "两 now() 同刻取值，仅时区表达不同");
        assertEquals(8, sh.getHour() - utc.getHour() < 0 ? sh.getHour() - utc.getHour() + 24 : sh.getHour() - utc.getHour());
    }

    @Test
    void test15_currentSeconds() {
        assertTrue(Math.abs(DateUtil.currentSeconds() - System.currentTimeMillis() / 1000) < 2);
    }

    @Test
    void test16_handwrittenPoolBoundedNamedCallerRuns() throws Exception {
        AtomicInteger seq = new AtomicInteger(1);
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
                2, 2, 0L, TimeUnit.MILLISECONDS,
                new LinkedBlockingQueue<>(100),
                r -> new Thread(r, "eval-pool-" + seq.getAndIncrement()),
                new ThreadPoolExecutor.CallerRunsPolicy());
        CountDownLatch latch = new CountDownLatch(10);
        ConcurrentLinkedQueue<String> names = new ConcurrentLinkedQueue<>();
        for (int i = 0; i < 10; i++) {
            pool.submit(() -> {
                names.add(Thread.currentThread().getName());
                latch.countDown();
            });
        }
        latch.await();
        pool.shutdown();
        assertTrue(pool.awaitTermination(5, TimeUnit.SECONDS));
        assertEquals(10, names.size());
        assertTrue(names.stream().allMatch(n -> n.startsWith("eval-pool-") || n.startsWith("main")));
    }

    @Test
    void test17_md5KnownVector() {
        assertEquals("e10adc3949ba59abbe56e057f20f883e", SecureUtil.md5("123456"));
    }

    @Test
    void test18_sha256KnownVector() {
        assertEquals(64, SecureUtil.sha256("123456").length());
        assertEquals("8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92",
                SecureUtil.sha256("123456"));
    }

    @Test
    void test19_bcryptSaltedVerify() {
        String hash = BCrypt.hashpw("s3cret");
        assertTrue(hash.startsWith("$2"));
        assertNotEquals(hash, BCrypt.hashpw("s3cret"));
        assertTrue(BCrypt.checkpw("s3cret", hash));
        assertFalse(BCrypt.checkpw("wrong", hash));
    }

    @Test
    void test20_base64RoundTrip() {
        byte[] raw = "达尔文评估 v3.5.0".getBytes();
        assertEquals("达尔文评估 v3.5.0",
                new String(cn.hutool.core.codec.Base64.decode(cn.hutool.core.codec.Base64.encode(raw))));
    }

    @Test
    void test21_handRolledHexLosesLeadingZero() {
        assertEquals(1, Integer.toHexString(0x0F).length());
        assertEquals("0f", String.format("%02x", 0x0F));
    }

    @Test
    void test22_md5Always32Hex() {
        for (String s : List.of("", "a", "0", "leading-zero-input", "中文输入")) {
            assertEquals(32, SecureUtil.md5(s).length());
        }
    }

    @Test
    void test23_randomIntHalfOpen() {
        int min = 0, maxSeen = 1_000_000 - 1;
        for (int i = 0; i < 100_000; i++) {
            int v = cn.hutool.core.util.RandomUtil.randomInt(100000, 1000000);
            assertTrue(v >= 100000 && v < 1000000, "randomInt 半开区间 [min,max)，实测值 " + v);
        }
        assertTrue(min < maxSeen);
    }

    @Test
    void test24_secureRandom6DigitCode() {
        SecureRandom sr = new SecureRandom();
        int code = sr.nextInt(900000) + 100000;
        assertTrue(code >= 100000 && code <= 999999);
    }
}
