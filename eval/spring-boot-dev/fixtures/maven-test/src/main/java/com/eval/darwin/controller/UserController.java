package com.eval.darwin.controller;

import com.eval.darwin.dto.UserCreateDTO;
import com.eval.darwin.dto.UserVO;
import com.eval.darwin.service.UserService;
import com.eval.darwin.common.Result;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

/**
 * 验证 02-layered-arch.md：Controller 只依赖 Service，返回 Result<UserVO>（非 Entity）。
 * 验证 04-validation.md：@Valid + @RequestBody Bean 校验；非 Bean 参数 @Min 须类级 @Validated。
 */
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
@Validated  // 非 Bean 参数（@RequestParam）校验须类级标注
public class UserController {

    private final UserService userService;

    @PostMapping
    public Result<UserVO> create(@Valid @RequestBody UserCreateDTO dto) {
        return Result.success(userService.create(dto));
    }

    @GetMapping("/search")
    public Result<?> search(@RequestParam @Min(1) Integer size) {
        return Result.success("ok");
    }
}
