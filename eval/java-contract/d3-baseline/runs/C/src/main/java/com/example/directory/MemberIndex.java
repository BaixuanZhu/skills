package com.example.directory;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/**
 * 成员目录索引工具（纯函数，全部 static）。
 *
 * <p>边界取舍按项目契约 .claude/rules/java-contract.md：
 * 空结果用 Optional / 空集合（不用 null）；集合参数 null 按空处理；
 * 集合内 null 元素跳过；操作所依赖字段无值的记录整条跳过；
 * 重复 id 保留首条（putIfAbsent）；返回集合不可变且保插入顺序。
 */
public final class MemberIndex {

    private MemberIndex() {
    }

    /**
     * 按 id 建索引。
     *
     * <p>id 无值的记录无法作为键，整条跳过；重复 id 保留首条。
     * 入参为 null 按空集合处理，返回空 Map（不用 null）。
     */
    public static Map<String, Member> index(List<Member> members) {
        Map<String, Member> byId = new LinkedHashMap<>();
        if (members != null) {
            for (Member member : members) {
                if (member == null || member.getId() == null) {
                    continue;
                }
                byId.putIfAbsent(member.getId(), member); // 重复 id 保留首条
            }
        }
        return Collections.unmodifiableMap(byId);
    }

    /**
     * 按 id 查单个成员，返回首个匹配（与 index 的首条语义一致）；无结果返回 {@link Optional#empty()}。
     *
     * <p>id 为必填标量，null 直接 {@link Objects#requireNonNull} fail fast；
     * members 为集合参数，null 按空处理。
     */
    public static Optional<Member> find(List<Member> members, String id) {
        Objects.requireNonNull(id, "id");
        if (members == null) {
            return Optional.empty();
        }
        for (Member member : members) {
            if (member != null && id.equals(member.getId())) {
                return Optional.of(member);
            }
        }
        return Optional.empty();
    }

    /**
     * 平均年龄；无任何有效记录时平均没有业务含义，返回 {@link Optional#empty()}（不是 0）。
     *
     * <p>age 无值的记录整条跳过；用 long 累加避免 int 溢出。重复 id 的记录按原样计入
     * （重复 key 保留首条仅约束以 id 为键的 index/find，聚合不做去重）。
     */
    public static Optional<Double> averageAge(List<Member> members) {
        if (members == null) {
            return Optional.empty();
        }
        long sum = 0;
        long count = 0;
        for (Member member : members) {
            if (member == null) {
                continue;
            }
            Integer age = member.getAge();
            if (age == null) {
                continue;
            }
            sum += age;
            count++;
        }
        return count == 0 ? Optional.empty() : Optional.of((double) sum / count);
    }

    /**
     * 按 team 分组，组内保持输入顺序；无结果返回空 Map（不用 null）。
     *
     * <p>team 无值的记录无法入组，整条跳过；分组是按 team 聚合而非按 id 建键，
     * 重复 id 的记录保留在各自组内。
     */
    public static Map<String, List<Member>> groupByTeam(List<Member> members) {
        Map<String, List<Member>> grouped = new LinkedHashMap<>();
        if (members != null) {
            for (Member member : members) {
                if (member == null || member.getTeam() == null) {
                    continue;
                }
                grouped.computeIfAbsent(member.getTeam(), team -> new ArrayList<>()).add(member);
            }
        }
        Map<String, List<Member>> result = new LinkedHashMap<>();
        for (Map.Entry<String, List<Member>> entry : grouped.entrySet()) {
            result.put(entry.getKey(), Collections.unmodifiableList(new ArrayList<>(entry.getValue())));
        }
        return Collections.unmodifiableMap(result);
    }
}
