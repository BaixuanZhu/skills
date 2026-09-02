package demo;

/**
 * 订单域常量类——验证 11-conventions §10「常量按共享范围放置」处方：
 * 被 ≥2 个包引用的阈值/配置 → 按域拆分的常量类（禁 Constants 万能类），
 * final 类 + private 构造禁实例化。
 */
public final class OrderConstants {

    /** 最大重试次数（阈值类常量） */
    public static final int MAX_RETRY = 3;

    /** 超时毫秒数（配置类常量，long 字面量用大写 L） */
    public static final long TIMEOUT_MS = 5000L;

    private OrderConstants() {
    }
}
