---
paths:
  - "**/*Controller.java"
  - "**/*Config*.java"
---
<!-- seeded: sa-token-dev@3.0.0 -->

# Sa-Token 项目约定

> 由 `sa-token-dev` 播种，可整文件重新生成。`paths` 决定加载时机，必须与项目实际文件名一致，写错是静默不加载。

## 事实

- token 风格 / 状态：⟨simple-uuid + Redis / JWT Simple / JWT Stateless / SaJwtUtil 直连⟩
- token 传递：⟨Cookie / Header（header 名 ⟨名⟩，前缀 ⟨无 / Bearer⟩）⟩
- 账号体系：⟨单体系 / 多体系 StpKit⟨: type 列表⟩⟩；设备区分：⟨无 / device=⟨值⟩⟩
- SSO：⟨无 / 模式一 / 模式二 / 模式三⟩
- timeout ⟨秒⟩ / active-timeout ⟨秒或 -1⟩；is-concurrent ⟨⟩ / is-share ⟨⟩
- 封禁：⟨不用 / StpUtil.disable，默认封 ⟨时长⟩，入口 ⟨类名⟩⟩
- 权限码命名：⟨如 user:delete⟩；权限/角色数据源：⟨StpInterface 实现类⟩
- 拦截收口：⟨SaInterceptor 注册类 / SaRouter 规则类⟩；白名单：⟨路径清单所在处⟩

## 流程（做完这一步才算完成）

- 新增受保护接口 → 确认落在注解或路由**一处**收口内；写完发一次不带 token 的请求，必须被拦
- 封禁 / 解封 → 先 kickout 再 disable，登录前 checkDisable；写完验旧 token 失效 + 新登录被拒
- 改权限码 → grep 注解/路由处同步改，别只改 StpInterface 数据源
- 前后端分离 → 登录响应必须带 tokenValue（本项目通道见「事实」）

## 边界

- 遇陷阱先看技能 `sa-token-dev` 的 `references/02-traps.md`；选型争议看 `01-decisions.md`
