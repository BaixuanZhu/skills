package com.example.demo;

import cn.dev33.satoken.stp.StpUtil;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 请求驱动的实跑验证端点（Sa-Token 1.46.0）。
 */
@RestController
public class TestController {

    @RequestMapping("doLogin")
    public String doLogin(Integer id) {
        StpUtil.login(id == null ? 10001 : id);
        return StpUtil.getTokenValue();
    }

    @RequestMapping("sessionOps")
    public String sessionOps() {
        var session = StpUtil.getSession();
        List<String> tags = session.getList("tagList", String.class, () -> List.of("a", "b"));
        Set<String> roles = session.getSet("roleSet", String.class, () -> Set.of("admin"));
        Map<String, Integer> scores = session.getMap("scoreMap", String.class, Integer.class,
                () -> Map.of("math", 90));
        List<String> cached = session.getList("tagList", String.class, () -> List.of("x"));
        return tags + "|" + roles + "|" + scores + "|cached=" + cached;
    }

    @RequestMapping("listenerLogout")
    public String listenerLogout(Integer id) {
        int before = MySaTokenListener.beforeLogoutCount;
        StpUtil.logout(id == null ? 10002 : id);
        return "beforeLogout delta=" + (MySaTokenListener.beforeLogoutCount - before);
    }

    @RequestMapping("sysUserOps")
    public String sysUserOps() {
        var session = StpUtil.getSession();
        SysUser user = new SysUser();
        user.name = "zhang";
        session.set("user", user);
        SysUser read = session.getModel("user", SysUser.class);
        return "name=" + read.name;
    }
}
