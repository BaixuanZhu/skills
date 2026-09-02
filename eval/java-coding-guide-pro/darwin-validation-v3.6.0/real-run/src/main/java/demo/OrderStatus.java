package demo;

/**
 * 订单状态枚举——验证 11-conventions §9「状态/类型码 → 枚举」处方：
 * 字面量 "PENDING" 出现 ≥2 处时提取为枚举，以枚举常量比较替代字符串比较。
 */
public enum OrderStatus {
    PENDING, PAID, CLOSED
}
