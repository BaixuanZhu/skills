package com.example.demo;

import cn.dev33.satoken.listener.SaTokenListenerForSimple;
import cn.dev33.satoken.stp.parameter.SaLoginParameter;
import cn.dev33.satoken.stp.parameter.SaLogoutParameter;

/**
 * 验证 skill 11-advanced §10 全局侦听器新增的注销前钩子（v1.46.0+）。
 */
public class MySaTokenListener extends SaTokenListenerForSimple {

    public static int beforeLogoutCount = 0;
    public static int beforeKickoutCount = 0;
    public static int beforeReplacedCount = 0;

    @Override
    public void doBeforeLogout(String loginType, Object loginId, String tokenValue, SaLogoutParameter logoutParameter) {
        beforeLogoutCount++;
    }

    @Override
    public void doBeforeKickout(String loginType, Object loginId, String tokenValue, SaLogoutParameter logoutParameter) {
        beforeKickoutCount++;
    }

    @Override
    public void doBeforeReplaced(String loginType, Object loginId, String tokenValue, SaLogoutParameter logoutParameter) {
        beforeReplacedCount++;
    }

    @Override
    public void doLogin(String loginType, Object loginId, String tokenValue, SaLoginParameter loginParameter) {
    }
}
