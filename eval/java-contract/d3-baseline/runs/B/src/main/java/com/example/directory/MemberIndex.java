package com.example.directory;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalDouble;
import java.util.Set;

/**
 * 成员名册索引。四个方法都是只依赖入参的纯函数，全部 {@code static}，类内不混用。
 *
 * <p>数据来自外部导入，质量不可信，四个方法共享同一套边界规则：
 * <ul>
 *   <li>集合参数 {@code null} 与空等价，按空集合处理，不抛异常；</li>
 *   <li>集合里的 {@code null} 元素跳过，不影响其余记录；</li>
 *   <li>无结果不返回 {@code null}：单条查询返回 {@link Optional}，索引/分组返回空集合，
 *       平均年龄返回 {@link OptionalDouble}（0 不是合法的平均值）；</li>
 *   <li>返回的集合不可变；返回的 {@code Map} 保插入顺序（按 key 首次出现顺序）。</li>
 * </ul>
 *
 * <p>细粒度规则（重复 id 保留首条、id/team 缺失的记录跳过、age 缺失不计入平均）
 * 见 {@code .claude/rules/java-contract.md}。
 */
public final class MemberIndex {

    private MemberIndex() {
    }

    /**
     * 按 id 建索引。id 缺失的记录不入索引；重复 id 保留首条。
     *
     * @param members 成员列表，{@code null} 与空等价
     * @return id → 成员，按 id 首次出现顺序、不可变；入参为空时返回空 Map
     */
    public static Map<String, Member> index(List<Member> members) {
        Map<String, Member> index = new LinkedHashMap<>();
        for (Member m : validMembers(members)) {
            // putIfAbsent：重复 key 保留首条，后到的记录不覆盖先到的
            index.putIfAbsent(m.getId(), m);
        }
        return Collections.unmodifiableMap(index);
    }

    /**
     * 按 id 查单个成员，命中重复 id 时返回首条。
     *
     * @param members 成员列表，{@code null} 与空等价
     * @param id      成员 id；{@code null} 抛 {@link NullPointerException}，
     *                空白抛 {@link IllegalArgumentException}（id 是定位参数，缺失即参数违规）
     * @return 找到的成员；不存在时 {@link Optional#empty()}，不返回 {@code null}
     */
    public static Optional<Member> find(List<Member> members, String id) {
        Objects.requireNonNull(id, "id");
        if (id.isBlank()) {
            throw new IllegalArgumentException("id must not be blank");
        }
        for (Member m : validMembers(members)) {
            if (id.equals(m.getId())) {
                return Optional.of(m);
            }
        }
        return Optional.empty();
    }

    /**
     * 平均年龄。age 缺失的记录跳过整条（不当 0 计入），重复 id 只计首条。
     *
     * @param members 成员列表，{@code null} 与空等价
     * @return 平均年龄；没有可计算的记录时 {@link OptionalDouble#empty()}（0 不是合法平均值）
     */
    public static OptionalDouble averageAge(List<Member> members) {
        long sum = 0;
        long count = 0;
        for (Member m : validMembers(members)) {
            Integer age = m.getAge();
            if (age == null) {
                continue;
            }
            sum += age;
            count++;
        }
        return count == 0 ? OptionalDouble.empty() : OptionalDouble.of((double) sum / count);
    }

    /**
     * 按 team 分组。team 缺失的记录无法归组，跳过；重复 id 只保留首条。
     *
     * @param members 成员列表，{@code null} 与空等价
     * @return team → 成员列表，按 team 首次出现顺序，Map 与内层 List 均不可变；入参为空时返回空 Map
     */
    public static Map<String, List<Member>> groupByTeam(List<Member> members) {
        Map<String, List<Member>> grouped = new LinkedHashMap<>();
        for (Member m : validMembers(members)) {
            String team = m.getTeam();
            if (team == null || team.isBlank()) {
                continue;
            }
            grouped.computeIfAbsent(team, k -> new ArrayList<>()).add(m);
        }
        Map<String, List<Member>> result = new LinkedHashMap<>();
        for (Map.Entry<String, List<Member>> entry : grouped.entrySet()) {
            result.put(entry.getKey(), List.copyOf(entry.getValue()));
        }
        return Collections.unmodifiableMap(result);
    }

    /**
     * 四个方法共享的有效成员集（先剔除再计算）：{@code null} 集合按空处理；
     * 跳过 {@code null} 元素与 id 缺失（null/空白）的记录；重复 id 保留首条；
     * 保持首次出现顺序。
     */
    private static List<Member> validMembers(List<Member> members) {
        if (members == null || members.isEmpty()) {
            return List.of();
        }
        List<Member> valid = new ArrayList<>(members.size());
        Set<String> seen = new HashSet<>();
        for (Member m : members) {
            if (m == null) {
                continue;
            }
            String id = m.getId();
            if (id == null || id.isBlank()) {
                continue;
            }
            if (seen.add(id)) {
                valid.add(m);
            }
        }
        return valid;
    }
}
