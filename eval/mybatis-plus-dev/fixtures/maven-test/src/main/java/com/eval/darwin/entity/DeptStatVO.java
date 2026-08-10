package com.eval.darwin.entity;

import lombok.Data;

/**
 * 聚合查询结果 VO（验证 Wrapper 能力边界 → XML 改写，强约束 #3）。
 * 聚合/计算列无对应实体属性，需独立 VO + resultMap 映射。
 */
@Data
public class DeptStatVO {
    private Long deptId;
    private Long userCount;
    private Integer avgAge;
    /** 窗口函数 ROW_NUMBER() 产出的计算列 */
    private Integer rowNum;
}
