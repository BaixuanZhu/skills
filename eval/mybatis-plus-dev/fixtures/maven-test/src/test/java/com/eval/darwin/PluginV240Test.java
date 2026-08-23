package com.eval.darwin;

import com.baomidou.mybatisplus.core.toolkit.sql.SqlInjectionUtils;
import com.baomidou.mybatisplus.extension.plugins.handler.MultiDataPermissionHandler;
import com.baomidou.mybatisplus.extension.plugins.inner.DataPermissionInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.DynamicTableNameInnerInterceptor;
import net.sf.jsqlparser.expression.Expression;
import net.sf.jsqlparser.expression.LongValue;
import net.sf.jsqlparser.expression.operators.relational.ExpressionList;
import net.sf.jsqlparser.expression.operators.relational.InExpression;
import net.sf.jsqlparser.schema.Column;
import net.sf.jsqlparser.schema.Table;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * v2.4.0 API 事实修正达尔文实跑验证（对照真实 MP 3.5.17 jar 重写的三处示例）：
 * - 07-plugin §4：DataPermissionInterceptor / MultiDataPermissionHandler 真实签名
 * - 07-plugin §3：DynamicTableNameInnerInterceptor 两参 TableNameHandler
 * - 强约束 #7 / 05 §5：SqlInjectionUtils.check 只返回 boolean、不抛异常
 * 纯单元级——被验证的正是技能示例的接口签名与 AST 构造，无需数据库。
 */
class PluginV240Test {

    // ========== 07-plugin §4：DataPermissionInterceptor 真实 API ==========

    /**
     * 验证 MultiDataPermissionHandler 真实签名 getSqlSegment(Table, Expression, String)
     * 返回单个 Expression（null=该表不追加）；InExpression 两参 + ExpressionList 构造可编译。
     * v2.3.1 误记为 getSqlSegment(ExecutionStatement) 返回 List&lt;DataPermissionRule&gt;（两类均不存在）。
     */
    @Test
    void dataPermission_真实API_返回单个Expression() {
        MultiDataPermissionHandler handler = new MultiDataPermissionHandler() {
            @Override
            public Expression getSqlSegment(Table table, Expression where, String mappedStatementId) {
                if (!"sys_user".equals(table.getName())) {
                    return null; // 非业务表不追加条件（防权限表自过滤）
                }
                List<Long> deptIds = Arrays.asList(100L, 200L);
                return new InExpression(new Column("dept_id"),
                        new ExpressionList(deptIds.stream().map(LongValue::new).toList()));
            }
        };
        assertNull(handler.getSqlSegment(new Table("sys_dict"), null, "selectById"),
                "非业务表应返回 null（不追加条件）");
        Expression cond = handler.getSqlSegment(new Table("sys_user"), null, "selectList");
        assertNotNull(cond);
        assertEquals(InExpression.class, cond.getClass());
        assertTrue(cond.toString().contains("dept_id"), "应生成 dept_id 条件，实际: " + cond);
        assertTrue(cond.toString().contains("100"), "应包含部门 100，实际: " + cond);
        assertNotNull(new DataPermissionInterceptor(handler), "带 handler 的构造器应存在");
    }

    // ========== 07-plugin §3：DynamicTableNameInnerInterceptor 两参 handler ==========

    /**
     * 验证 TableNameHandler.dynamicTableName(String sql, String tableName) 是两参函数式接口
     * （v2.3.1 误写单参 lambda，不匹配接口签名无法编译）；两参 handler 表名替换生效。
     */
    @Test
    void dynamicTableName_两参handler_表名替换生效() {
        DynamicTableNameInnerInterceptor interceptor = new DynamicTableNameInnerInterceptor(
                (sql, tableName) -> "user".equals(tableName)
                        ? "user_" + LocalDate.now().getMonthValue()
                        : tableName);
        String rewritten = interceptor.changeTable("SELECT * FROM user");
        assertTrue(rewritten.contains("user_" + LocalDate.now().getMonthValue()),
                "应替换为按月表名，实际: " + rewritten);
    }

    // ========== 强约束 #7 / 05 §5：SqlInjectionUtils.check 语义 ==========

    /**
     * 验证 check(String) 只返回 boolean、自身不抛异常
     * （v2.3.1 误记「返回 boolean 并抛异常」——裸调用会导致返回值被忽略、校验形同虚设）。
     */
    @Test
    void sqlInjectionUtils_check只返回boolean_不抛异常() {
        assertTrue(SqlInjectionUtils.check("1' OR '1'='1"), "注入特征串应返回 true（且不抛异常）");
        assertFalse(SqlInjectionUtils.check("2024-01-01"), "正常日期串应返回 false");
        // 技能修正后的调用方拦截模式：check 拦截 + 占位符传原值
        String inputDate = "2024-01-01";
        if (SqlInjectionUtils.check(inputDate)) {
            throw new IllegalArgumentException("非法输入");
        }
        // 正常输入走到此处 = 未被误拦
    }
}
