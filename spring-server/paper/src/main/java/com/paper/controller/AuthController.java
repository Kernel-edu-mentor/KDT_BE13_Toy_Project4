package com.paper.controller;

import com.paper.domain.User;
import com.paper.dto.user.KakaoCallbackRequest;
import com.paper.dto.user.LoginRequest;
import com.paper.dto.user.LoginResponse;
import com.paper.dto.user.UserRegistrationRequest;
import com.paper.dto.user.UserResponse;
import com.paper.repository.UserRepository;
import com.paper.security.UserPrincipal;
import com.paper.service.KakaoService;
import com.paper.service.UserService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final UserService userService;
    private final UserRepository userRepository;
    private final KakaoService kakaoService;

    @PostMapping("/register")
    public ResponseEntity<UserResponse> register(@Valid @RequestBody UserRegistrationRequest request) {
        UserResponse response = userService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(
            @Valid @RequestBody LoginRequest request,
            HttpServletRequest httpRequest
    ) {
        Authentication authentication = userService.authenticate(request);

        SecurityContextHolder.getContext().setAuthentication(authentication);

        HttpSession session = httpRequest.getSession(true);
        session.setAttribute(HttpSessionSecurityContextRepository.SPRING_SECURITY_CONTEXT_KEY,
                SecurityContextHolder.getContext());

        UserPrincipal principal = (UserPrincipal) authentication.getPrincipal();
        UserResponse userResponse = userService.getUserProfile(principal.getUsername());
        return ResponseEntity.ok(LoginResponse.of(session.getId(), userResponse));
    }

    @PostMapping("/kakao/callback")
    public ResponseEntity<LoginResponse> handleKakaoCallback(
            @Valid @RequestBody KakaoCallbackRequest request,
            HttpServletRequest httpRequest
    ) {
        // 1. 인가 코드를 access_token으로 교환
        String accessToken = kakaoService.exchangeCodeForToken(request.getCode());

        // 2. access_token으로 사용자 정보 조회 및 자동 회원가입/로그인
        UserResponse userResponse = userService.loginWithKakao(accessToken);

        // 3. 카카오 로그인 사용자는 비밀번호 인증 없이 직접 인증 처리
        User user = userRepository.findByUsername(userResponse.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));
        UserPrincipal principal = UserPrincipal.from(user);

        Authentication authentication = new UsernamePasswordAuthenticationToken(
                principal,
                null,
                principal.getAuthorities()
        );

        SecurityContextHolder.getContext().setAuthentication(authentication);

        HttpSession session = httpRequest.getSession(true);
        session.setAttribute(HttpSessionSecurityContextRepository.SPRING_SECURITY_CONTEXT_KEY,
                SecurityContextHolder.getContext());

        // 4. 로그아웃 시 사용할 수 있도록 accessToken을 세션에 저장
        session.setAttribute("kakao_access_token", accessToken);

        return ResponseEntity.ok(LoginResponse.of(session.getId(), userResponse));
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(HttpServletRequest httpRequest) {
        HttpSession session = httpRequest.getSession(false);

        if (session != null) {
            // 카카오 로그아웃 처리
            String accessToken = (String) session.getAttribute("kakao_access_token");
            if (accessToken != null) {
                kakaoService.logout(accessToken);
            }

            // 세션 무효화
            session.invalidate();
        }

        // SecurityContext 정리
        SecurityContextHolder.clearContext();

        return ResponseEntity.ok().build();
    }

    @GetMapping("/me")
    public ResponseEntity<UserResponse> me(@AuthenticationPrincipal UserPrincipal principal) {
        if (principal == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Authentication required");
        }
        UserResponse response = userService.getUserProfile(principal.getUsername());
        return ResponseEntity.ok(response);
    }
}
