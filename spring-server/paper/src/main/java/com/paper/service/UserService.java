package com.paper.service;

import com.paper.domain.User;
import com.paper.dto.user.LoginRequest;
import com.paper.dto.user.UserRegistrationRequest;
import com.paper.dto.user.UserResponse;
import com.paper.exception.InvalidCredentialsException;
import com.paper.exception.UsernameAlreadyExistsException;
import com.paper.repository.UserRepository;
import com.paper.security.UserPrincipal;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final KakaoService kakaoService;

    @Transactional
    public UserResponse register(UserRegistrationRequest request) {
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new UsernameAlreadyExistsException(request.getUsername());
        }

        User user = User.builder()
                .username(request.getUsername())
                .password(passwordEncoder.encode(request.getPassword()))
                .role(request.resolveRole())
                .createdAt(LocalDateTime.now())
                .build();

        User saved = userRepository.save(user);
        return UserResponse.from(saved);
    }

    public Authentication authenticate(LoginRequest request) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getUsername(), request.getPassword())
        );

        if (!(authentication.getPrincipal() instanceof UserPrincipal)) {
            throw new InvalidCredentialsException();
        }
        return authentication;
    }

    public UserResponse getUserProfile(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(InvalidCredentialsException::new);
        return UserResponse.from(user);
    }

    @Transactional
    public UserResponse loginWithKakao(String accessToken) {
        KakaoService.KakaoUserInfo kakaoUserInfo = kakaoService.getUserInfo(accessToken);
        String kakaoId = "kakao_" + kakaoUserInfo.getId();
        String username = kakaoUserInfo.getKakaoAccount() != null &&
                kakaoUserInfo.getKakaoAccount().getEmail() != null
                ? kakaoUserInfo.getKakaoAccount().getEmail()
                : kakaoId;

        User user = userRepository.findByUsername(username)
                .orElseGet(() -> {
                    log.info("카카오 로그인 신규 사용자 회원가입: {}", username);
                    User newUser = User.builder()
                            .username(username)
                            .password(passwordEncoder.encode("kakao_" + kakaoUserInfo.getId())) // 임시 비밀번호
                            .role(User.Role.STUDENT)
                            .createdAt(LocalDateTime.now())
                            .build();
                    return userRepository.save(newUser);
                });
        return UserResponse.from(user);
    }
}
