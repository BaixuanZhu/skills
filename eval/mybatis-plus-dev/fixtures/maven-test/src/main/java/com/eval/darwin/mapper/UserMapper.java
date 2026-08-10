package com.eval.darwin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.eval.darwin.entity.DeptStatVO;
import com.eval.darwin.entity.UserDO;
import org.apache.ibatis.annotations.Param;

/**
 * Mapper（验证继承范式 + Wrapper 能力边界 → XML）。
 * - extends BaseMapper<UserDO>：单表 CRUD 走父类方法（强约束 #1/#2）
 * - selectDeptStat / selectUserPage：聚合/窗口/联表走 XML（强约束 #3）
 */
public interface UserMapper extends BaseMapper<UserDO> {

    /**
     * 聚合 + GROUP BY 查询（强约束 #3：Wrapper 表达不了，进 XML）。
     * 按 dept_id 分组统计用户数 + 平均年龄，筛选用户数 > 阈值的部门。
     */
    DeptStatVO selectDeptStat(@Param("minCount") int minCount);

    /**
     * 窗口函数查询（强约束 #3：ROW_NUMBER() OVER 走 XML）。
     * 取每个部门年龄最大的用户（row_num = 1）。
     */
    java.util.List<DeptStatVO> selectTopUserPerDept();

    /**
     * 联表分页（强约束 #3 + 06-page.md §4：IPage 入参非 null）。
     */
    IPage<DeptStatVO> selectDeptStatPage(IPage<DeptStatVO> page, @Param("minCount") int minCount);
}
