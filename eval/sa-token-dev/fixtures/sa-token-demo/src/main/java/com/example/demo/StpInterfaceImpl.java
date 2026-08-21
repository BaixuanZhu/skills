package com.example.demo;

import cn.dev33.satoken.model.wrapperInfo.SaDisableWrapperInfo;
import cn.dev33.satoken.stp.StpInterface;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 验证 skill 11-advanced §3.5 isDisabled 三参签名（v1.46.0 破坏性变更）。
 * StpInterface 接口在 v1.46.0 起为 isDisabled(loginId, service, loginType)。
 */
@Component
public class StpInterfaceImpl implements StpInterface {

    @Override
    public List<String> getPermissionList(Object loginId, String loginType) {
        return List.of("user:edit");
    }

    @Override
    public List<String> getRoleList(Object loginId, String loginType) {
        return List.of("admin");
    }

    @Override
    public SaDisableWrapperInfo isDisabled(Object loginId, String service, String loginType) {
        // skill 11-advanced §3.5 正例：v1.46.0+ 三参
        return SaDisableWrapperInfo.createNotDisabled();
    }
}
