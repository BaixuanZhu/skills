package com.example.directory;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalDouble;

/**
 * 成员目录索引工具。
 *
 * <p>数据来自外部导入、质量不可信，故对以下边界情况做了显式处理（详见 {@code response.md}）：</p>
 * <ul>
 *   <li>入参 {@code members} 为 {@code null}：按空集合处理；</li>
 *   <li>集合内含 {@code null} 元素：跳过；</li>
 *   <li>成员 {@code id} 为 {@code null}：不进入 id 索引/查找；</li>
 *   <li>重复 {@code id}：以首次出现者生效（index 与 find 保持一致）；</li>
 *   <li>成员 {@code age} 为 {@code null}：不参与平均年龄计算；</li>
 *   <li>成员 {@code team} 为 {@code null}：归入 {@code ""}（未分组）桶。</li>
 * </ul>
 *
 * <p>所有方法均为无状态静态工具方法，返回值尽量不可变、且用 {@code Optional} 表达“可能无结果”。</p>
 */
public final class MemberIndex {

    /** 无 team 成员的分组键（“未分组”桶）。 */
    private static final String NO_TEAM = "";

    private MemberIndex() {
        // 工具类，禁止实例化
    }

    /**
     * 按 id 建立索引（id -> 成员）。
     *
     * <ul>
     *   <li>{@code members} 为 {@code null} 或空：返回空索引；</li>
     *   <li>跳过 {@code null} 元素与 {@code id} 为 {@code null} 的成员；</li>
     *   <li>重复 id：保留首次出现的成员（{@code putIfAbsent}）。</li>
     * </ul>
     *
     * @param members 成员列表，可为 {@code null}
     * @return 不可变索引；键的迭代顺序为 id 首次出现顺序
     */
    public static Map<String, Member> index(List<Member> members) {
        Map<String, Member> index = new LinkedHashMap<>();
        if (members == null) {
            return Collections.unmodifiableMap(index);
        }
        for (Member m : members) {
            if (m == null || m.getId() == null) {
                continue;
            }
            index.putIfAbsent(m.getId(), m);
        }
        return Collections.unmodifiableMap(index);
    }

    /**
     * 查找单个成员。
     *
     * <ul>
     *   <li>{@code members} 为 {@code null} 或空、或 {@code id} 为 {@code null}：返回 {@link Optional#empty()}；</li>
     *   <li>跳过 {@code null} 元素；</li>
     *   <li>重复 id：返回首次出现的成员，与 {@link #index(List)} 保持一致。</li>
     * </ul>
     *
     * @param members 成员列表，可为 {@code null}
     * @param id      要查找的 id，可为 {@code null}
     * @return 首个 id 匹配的成员；不存在则为空
     */
    public static Optional<Member> find(List<Member> members, String id) {
        if (members == null || id == null) {
            return Optional.empty();
        }
        for (Member m : members) {
            if (m != null && id.equals(m.getId())) {
                return Optional.of(m);
            }
        }
        return Optional.empty();
    }

    /**
     * 计算平均年龄。
     *
     * <ul>
     *   <li>{@code members} 为 {@code null} 或空：返回 {@link OptionalDouble#empty()}；</li>
     *   <li>跳过 {@code null} 元素与 {@code age} 为 {@code null} 的成员（缺失年龄不计为 0）；</li>
     *   <li>若无任何有效年龄：返回 {@link OptionalDouble#empty()}（均值无定义）。</li>
     * </ul>
     *
     * @param members 成员列表，可为 {@code null}
     * @return 已知年龄成员的算术平均值；无可计算项时为空
     */
    public static OptionalDouble averageAge(List<Member> members) {
        if (members == null) {
            return OptionalDouble.empty();
        }
        long sum = 0;
        long count = 0;
        for (Member m : members) {
            if (m == null || m.getAge() == null) {
                continue;
            }
            sum += m.getAge();
            count++;
        }
        if (count == 0) {
            return OptionalDouble.empty();
        }
        return OptionalDouble.of((double) sum / count);
    }

    /**
     * 按 team 分组。
     *
     * <ul>
     *   <li>{@code members} 为 {@code null} 或空：返回空分组；</li>
     *   <li>跳过 {@code null} 元素；</li>
     *   <li>{@code team} 为 {@code null} 的成员归入键 {@code ""}（未分组）桶，
     *       与 {@code team} 本身为 {@code ""} 的成员同桶，避免 {@code null} 键带来的
     *       {@code Map.copyOf} 等实现层面的隐患；</li>
     *   <li>各组内成员保持原列表顺序，键按 team 首次出现顺序排列。</li>
     * </ul>
     *
     * @param members 成员列表，可为 {@code null}
     * @return 不可变映射（team -> 该组成员），内层列表亦不可变
     */
    public static Map<String, List<Member>> groupByTeam(List<Member> members) {
        Map<String, List<Member>> groups = new LinkedHashMap<>();
        if (members == null) {
            return Collections.unmodifiableMap(groups);
        }
        for (Member m : members) {
            if (m == null) {
                continue;
            }
            String team = m.getTeam() == null ? NO_TEAM : m.getTeam();
            groups.computeIfAbsent(team, k -> new ArrayList<>()).add(m);
        }
        Map<String, List<Member>> result = new LinkedHashMap<>();
        for (Map.Entry<String, List<Member>> e : groups.entrySet()) {
            result.put(e.getKey(), Collections.unmodifiableList(e.getValue()));
        }
        return Collections.unmodifiableMap(result);
    }
}
