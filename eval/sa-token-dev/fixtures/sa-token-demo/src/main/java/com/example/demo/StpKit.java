package com.example.demo;

import cn.dev33.satoken.stp.StpLogic;
import cn.dev33.satoken.stp.StpUtil;

/**
 * StpLogic 门面类（官方文档模式，用户自定义）——管理多套账号体系。
 * skill 11-advanced §6 多账号门面模式。
 */
public class StpKit {

    public static final StpLogic DEFAULT = StpUtil.stpLogic;

    public static final StpLogic ADMIN = new StpLogic("admin");

    public static final StpLogic USER = new StpLogic("user");
}
