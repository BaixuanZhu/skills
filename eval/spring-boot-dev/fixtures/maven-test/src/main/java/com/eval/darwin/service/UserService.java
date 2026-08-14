package com.eval.darwin.service;

import com.eval.darwin.dto.UserCreateDTO;
import com.eval.darwin.dto.UserVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 验证 06-transaction.md 坑 1（自调用失效）+ 强约束 3（rollbackFor = Exception.class）。
 *
 * ⚠️ 达尔文发现：@Lazy 自注入不能配 @RequiredArgsConstructor（Lombok 不传 @Lazy 到构造器参数），
 *    必须手写构造器。否则启动报 BeanCurrentlyInCreationException（循环依赖）。
 */
@Slf4j
@Service
public class UserService {

    private final UserService self;

    // 手写构造器：@Lazy 必须在构造器参数上（@RequiredArgsConstructor 生成的构造器不会传 @Lazy）
    public UserService(@Lazy UserService self) {
        this.self = self;
    }

    public UserVO create(UserCreateDTO dto) {
        log.info("创建用户: {}", dto.getUsername());
        // 同类内事务方法调用须用 self.xxx()（走代理），而非 this.xxx()（绕过代理，事务失效）
        self.insert(dto.getUsername());
        return new UserVO();
    }

    @Transactional(rollbackFor = Exception.class)  // 默认只回滚 RuntimeException，须显式 rollbackFor
    public void insert(String username) {
        log.info("insert: {}", username);
    }
}
