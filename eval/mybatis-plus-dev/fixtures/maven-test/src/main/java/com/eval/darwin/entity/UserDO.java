package com.eval.darwin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.eval.darwin.enums.GenderEnum;
import lombok.Data;
import lombok.experimental.Accessors;

/**
 * 实体类（供 Lambda 方法引用 UserDO::getXxx）。
 * 用 @Accessors(chain=true) 支持 new UserDO().setXxx().setYyy() 链式。
 */
@Data
@Accessors(chain = true)
@TableName("sys_user")
public class UserDO {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private Integer age;

    private Integer status;

    /** 枚举字段：MP 据 @EnumValue 映射 code（见 GenderEnum） */
    private GenderEnum gender;

    private Long deptId;

    private Integer deleted;

    private Integer version;
}
